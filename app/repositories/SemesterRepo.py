from typing import Optional

from sqlalchemy.orm import Query, Session

from models.Semesters import Semester


class SemesterRepo:
    @staticmethod
    def base_query(db: Session) -> Query:
        return db.query(Semester)

    @staticmethod
    def get_by_id(db: Session, ma_hoc_ky: str) -> Optional[Semester]:
        return db.query(Semester).filter(Semester.MaHocKy == ma_hoc_ky).first()
