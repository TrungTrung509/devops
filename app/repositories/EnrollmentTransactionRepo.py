import json
from datetime import datetime

from sqlalchemy.orm import Session

from configs.db import SessionLocals
from enums.status import EnrollmentTransactionState
from models.EnrollmentTransactions import EnrollmentTransaction
from services.enrollment_3pc.context import Enrollment3PCContext
from services.enrollment_3pc.db import Enrollment3PCDB


class EnrollmentTransactionRepo:
    @staticmethod
    def create_or_reset_rows(
        ctx: Enrollment3PCContext,
        sessions: dict[str, Session],
    ) -> None:
        payload_json = json.dumps(ctx.payload(), ensure_ascii=False)
        for site in ctx.transaction_sites:
            session = sessions[site]
            row = EnrollmentTransactionRepo.get_by_txn_and_site(session, ctx.txn_id, site)
            if row is None:
                row = EnrollmentTransaction(
                    TxnId=ctx.txn_id,
                    CoordinatorSite=ctx.coordinator_site,
                    SiteId=site,
                    UserId=ctx.user_id,
                    Action=ctx.action,
                    State=EnrollmentTransactionState.INIT,
                    TargetMaLopHP=ctx.target_ma_lop_hp,
                    TargetMaHP=ctx.target_ma_hp,
                    TargetMaHocKy=ctx.target_ma_hoc_ky,
                    OldMaLopHP=ctx.old_ma_lop_hp,
                    Payload=payload_json,
                    Message="Khoi tao giao dich 3PC",
                )
                session.add(row)
            else:
                row.State = EnrollmentTransactionState.INIT
                row.Payload = payload_json
                row.Message = "Khoi tao lai giao dich 3PC"
            session.flush()

    @staticmethod
    def set_state(
        ctx: Enrollment3PCContext,
        sessions: dict[str, Session],
        state: EnrollmentTransactionState,
        message: str,
    ) -> None:
        for site in ctx.transaction_sites:
            session = sessions[site]
            row = EnrollmentTransactionRepo.get_by_txn_and_site(session, ctx.txn_id, site)
            if row is None:
                raise LookupError(f"Khong tim thay giao dich 3PC tai {site}")
            if row.State == EnrollmentTransactionState.COMMITTED:
                continue
            row.State = state
            row.Message = message
            session.flush()

    @staticmethod
    def mark_aborted(
        ctx: Enrollment3PCContext,
        sessions: dict[str, Session],
        message: str,
    ) -> None:
        for site in ctx.transaction_sites:
            session = sessions.get(site)
            if session is None:
                continue
            
            # 1. Rollback toàn bộ dữ liệu nghiệp vụ (cùng các khóa Row Lock)
            session.rollback()
            
            # 2. Ghi nhận trạng thái ABORTED vào log trên một Transaction mới sạch sẽ
            try:
                row = EnrollmentTransactionRepo.get_by_txn_and_site(session, ctx.txn_id, site)
                if row is None or row.State == EnrollmentTransactionState.COMMITTED:
                    continue
                row.State = EnrollmentTransactionState.ABORTED
                row.Message = message
                session.commit()
            except Exception:
                session.rollback()

    @staticmethod
    def load_context(txn_id: str) -> Enrollment3PCContext | None:
        for site in SessionLocals:
            if not Enrollment3PCDB.is_site_alive(site):
                continue
            session = SessionLocals[site]()
            try:
                row = session.query(EnrollmentTransaction).filter(
                    EnrollmentTransaction.TxnId == txn_id
                ).first()
                if row is not None:
                    return Enrollment3PCContext.from_payload(json.loads(row.Payload))
            finally:
                session.close()
        return None

    @staticmethod
    def has_state(txn_id: str, state: EnrollmentTransactionState) -> bool:
        for site in SessionLocals:
            if not Enrollment3PCDB.is_site_alive(site):
                continue
            session = SessionLocals[site]()
            try:
                row = session.query(EnrollmentTransaction).filter(
                    EnrollmentTransaction.TxnId == txn_id,
                    EnrollmentTransaction.State == state,
                ).first()
                if row is not None:
                    return True
            finally:
                session.close()
        return False

    @staticmethod
    def collect_recovery_candidates(cutoff: datetime) -> tuple[set[str], set[str]]:
        pending_commit: set[str] = set()
        stale_abort: set[str] = set()

        for site in SessionLocals:
            if not Enrollment3PCDB.is_site_alive(site):
                continue
            session = SessionLocals[site]()
            try:
                precommit_rows = (
                    session.query(EnrollmentTransaction)
                    .filter(EnrollmentTransaction.State == EnrollmentTransactionState.PRECOMMIT)
                    .all()
                )
                pending_commit.update(row.TxnId for row in precommit_rows)

                stale_rows = (
                    session.query(EnrollmentTransaction)
                    .filter(
                        EnrollmentTransaction.State.in_(
                            [
                                EnrollmentTransactionState.INIT,
                                EnrollmentTransactionState.PREPARED,
                            ]
                        ),
                        EnrollmentTransaction.UpdatedAt < cutoff,
                    )
                    .all()
                )
                stale_abort.update(row.TxnId for row in stale_rows)
            finally:
                session.close()

        stale_abort.difference_update(pending_commit)
        return pending_commit, stale_abort

    @staticmethod
    def find_stale_for_resource(
        user_id: str,
        cutoff: datetime,
    ) -> tuple[set[str], set[str]]:
        """
        Tìm các giao dịch in-doubt liên quan đến user_id.
        - pending_commit: trạng thái PRECOMMIT → phải ép commit bất kể thời gian.
        - stale_abort:   trạng thái INIT/PREPARED quá hạn cutoff → có thể abort.
        """
        pending_commit: set[str] = set()
        stale_abort: set[str] = set()

        for site in SessionLocals:
            if not Enrollment3PCDB.is_site_alive(site):
                continue
            session = SessionLocals[site]()
            try:
                precommit_rows = session.query(EnrollmentTransaction).filter(
                    EnrollmentTransaction.State == EnrollmentTransactionState.PRECOMMIT,
                    EnrollmentTransaction.UserId == user_id,
                ).all()
                pending_commit.update(row.TxnId for row in precommit_rows)

                stale_rows = session.query(EnrollmentTransaction).filter(
                    EnrollmentTransaction.State.in_([
                        EnrollmentTransactionState.INIT,
                        EnrollmentTransactionState.PREPARED,
                    ]),
                    EnrollmentTransaction.UserId == user_id,
                    EnrollmentTransaction.UpdatedAt < cutoff,
                ).all()
                stale_abort.update(row.TxnId for row in stale_rows)
            finally:
                session.close()

        stale_abort.difference_update(pending_commit)
        return pending_commit, stale_abort

    @staticmethod
    def get_by_txn_and_site(
        session: Session,
        txn_id: str,
        site_id: str,
        *,
        for_update: bool = False,
    ) -> EnrollmentTransaction | None:
        query = session.query(EnrollmentTransaction).filter(
            EnrollmentTransaction.TxnId == txn_id,
            EnrollmentTransaction.SiteId == site_id,
        )
        if for_update:
            query = query.with_for_update()
        return query.first()
