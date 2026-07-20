from sqlalchemy.orm import Session
from enums.status import RecoveryAction, LogStatus
from models.RecoveryLogs import RecoveryLog

class RecoveryLogRepo:
    @staticmethod
    def append_recovery_log(
        db: Session,
        *,
        txn_id: str,
        user_id: str | None = None,
        ma_lop_hp: str | None = None,
        action: RecoveryAction,
        ma_co_so: str | None = None,
        status: LogStatus = LogStatus.SUCCESS,
        message: str | None = None,
    ) -> RecoveryLog:
        log = RecoveryLog(
            TxnId=txn_id,
            userId=user_id,
            MaLopHP=ma_lop_hp,
            Action=action,
            MaCoSo=ma_co_so,
            Status=status,
            Message=message,
        )

        db.add(log)
        db.commit()
        db.refresh(log)
        return log
