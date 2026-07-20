from typing import Optional

from sqlalchemy.orm import Query, Session

from models.Schedules import Schedule


class ScheduleRepo:
    @staticmethod
    def base_query(db: Session) -> Query:
        return db.query(Schedule)

    @staticmethod
    def get_by_id(db: Session, ma_lich: str) -> Optional[Schedule]:
        return db.query(Schedule).filter(Schedule.MaLich == ma_lich).first()
