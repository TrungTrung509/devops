import json
import asyncio
import uuid
from fastapi import HTTPException
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from configs.config import KAFKA_BOOTSTRAP_SERVERS
from schemas.Enrollment import EnrollmentCreate, RegistrationResult

class KafkaQueueService:
    producer: AIOKafkaProducer = None
    consumer: AIOKafkaConsumer = None
    pending_futures: dict[str, asyncio.Future] = {}
    consumer_task: asyncio.Task = None
    _started: bool = False

    @classmethod
    async def start(cls):
        if cls._started:
            return
        
        cls.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await cls.producer.start()

        cls.consumer = AIOKafkaConsumer(
            "registration_replies",
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="api_gateway_group",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest"
        )
        await cls.consumer.start()

        cls._started = True
        cls.consumer_task = asyncio.create_task(cls._listen_for_replies())

    @classmethod
    async def stop(cls):
        if not cls._started:
            return
        
        cls._started = False
        if cls.consumer_task:
            cls.consumer_task.cancel()
            try:
                await cls.consumer_task
            except asyncio.CancelledError:
                pass
        
        if cls.producer:
            await cls.producer.stop()
        if cls.consumer:
            await cls.consumer.stop()
        

    @classmethod
    async def _listen_for_replies(cls):
        try:
            async for msg in cls.consumer:
                payload = msg.value
                correlation_id = payload.get("correlation_id")
                if correlation_id and correlation_id in cls.pending_futures:
                    fut = cls.pending_futures.get(correlation_id)
                    if fut and not fut.done():
                        fut.set_result(payload.get("result"))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in KafkaQueueService reply listener: {e}")

    @classmethod
    async def publish_and_wait(cls, user, enroll_in: EnrollmentCreate, timeout: float = 10.0) -> RegistrationResult:
        if not cls._started:
            raise RuntimeError("KafkaQueueService has not been started.")

        correlation_id = str(uuid.uuid4())
        fut = asyncio.get_running_loop().create_future()
        cls.pending_futures[correlation_id] = fut

        user_data = {
            "userId": user.userId,
            "MaCoSo": user.MaCoSo,
            "username": user.username,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role)
        }

        payload = {
            "correlation_id": correlation_id,
            "user": user_data,
            "enroll_in": enroll_in.model_dump()
        }

        try:
        
            partition_key = enroll_in.MaLopHP or correlation_id
            await cls.producer.send_and_wait("registration_requests", payload, key=partition_key)
            # Wait for response
            result_dict = await asyncio.wait_for(fut, timeout=timeout)
            return RegistrationResult(**result_dict)
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Yêu cầu đăng ký đang được xử lý hoặc quá thời gian chờ (Gateway Timeout)."
            )
        finally:
            cls.pending_futures.pop(correlation_id, None)
