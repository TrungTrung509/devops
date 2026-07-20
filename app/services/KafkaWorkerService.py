import json
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from configs.config import KAFKA_BOOTSTRAP_SERVERS
from services.EnrollmentService import EnrollmentService
from schemas.Enrollment import EnrollmentCreate
from enums.user_role import UserRole
from fastapi import HTTPException

NUM_WORKERS = 8


class UserMock:
    def __init__(self, userId: str, MaCoSo: str, username: str, role: str):
        self.userId = userId
        self.MaCoSo = MaCoSo
        self.username = username
        try:
            self.role = UserRole(role)
        except ValueError:
            self.role = UserRole.SinhVien


class KafkaWorkerService:
    producer: AIOKafkaProducer = None
    worker_tasks: list[asyncio.Task] = []
    semaphore: asyncio.Semaphore = None
    _started: bool = False

    @classmethod
    async def start(cls):
        if cls._started:
            return

        cls.semaphore = asyncio.Semaphore(20)
        cls.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await cls.producer.start()

        cls._started = True
        cls.worker_tasks = [
            asyncio.create_task(cls._worker_loop(i), name=f"kafka-worker-{i}")
            for i in range(NUM_WORKERS)
        ]
        print(f"KafkaWorkerService started with {NUM_WORKERS} workers.")

    @classmethod
    async def stop(cls):
        if not cls._started:
            return

        cls._started = False
        for task in cls.worker_tasks:
            task.cancel()

        results = await asyncio.gather(*cls.worker_tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                print(f"Worker shutdown error: {result}")

        cls.worker_tasks = []
        if cls.producer:
            await cls.producer.stop()

    @classmethod
    async def _worker_loop(cls, worker_id: int):
        """Each worker has its own consumer in the same group so Kafka
        distributes partitions across them automatically."""
        consumer = AIOKafkaConsumer(
            "registration_requests",
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="registration_worker_group",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        await consumer.start()
        try:
            async for msg in consumer:
                payload = msg.value
                correlation_id = payload.get("correlation_id")
                if not correlation_id:
                    continue
                asyncio.create_task(cls._handle(correlation_id, payload))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[Worker-{worker_id}] Consumer loop crashed: {e}")
        finally:
            try:
                await consumer.stop()
            except Exception:
                pass

    @classmethod
    async def _handle(cls, correlation_id: str, payload: dict):
        user_data = payload.get("user", {})
        enroll_in_data = payload.get("enroll_in", {})
        ma_lop = enroll_in_data.get("MaLopHP")

        try:
            user = UserMock(**{
                "userId": user_data.get("userId"),
                "MaCoSo": user_data.get("MaCoSo"),
                "username": user_data.get("username", ""),
                "role": user_data.get("role", "SinhVien"),
            })
            enroll_in = EnrollmentCreate(**enroll_in_data)
            async with cls.semaphore:
                result = await asyncio.to_thread(EnrollmentService.register, user, enroll_in)
            result_dict = result.model_dump()
        except HTTPException as exc:
            result_dict = {"MaLopHP": ma_lop, "status": "Failed", "message": exc.detail, "error_code": "REGISTRATION_HTTP_ERROR", "reasons": [exc.detail]}
        except Exception as exc:
            result_dict = {"MaLopHP": ma_lop, "status": "Failed","message": f"System error: {exc}", "error_code": "REGISTRATION_SYSTEM_ERROR","reasons": [str(exc)]}

        try:
            await cls.producer.send_and_wait("registration_replies", {"correlation_id": correlation_id, "result": result_dict})
        except Exception as e:
            print(f"Failed to publish reply for {correlation_id}: {e}")
