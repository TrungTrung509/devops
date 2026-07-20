from typing import Optional

from sqlalchemy.orm import Query, Session

from models.Classrooms import Classroom
from schemas.Classroom import ClassroomFilter


class ClassroomRepo:
    @staticmethod
    def base_query(db: Session) -> Query:
        return db.query(Classroom)

    @staticmethod
    def get_by_id(db: Session, ma_phong: str) -> Optional[Classroom]:
        return db.query(Classroom).filter(Classroom.MaPhong == ma_phong).first()

    @staticmethod
    def apply_filters(query: Query, filters: Optional[ClassroomFilter]) -> Query:
        if not filters:
            return query

        if filters.keyword and filters.keyword.strip():
            keyword = filters.keyword.strip()
            # Tìm kiếm theo mã phòng hoặc tên phòng
            keyword_lower = keyword.lower()
            query = query.filter(
                (Classroom.MaPhong.ilike(f"%{keyword_lower}%")) |
                (Classroom.TenPhong.ilike(f"%{keyword_lower}%"))
            )

        if filters.LoaiPhong:
            query = query.filter(Classroom.LoaiPhong == filters.LoaiPhong)

        if filters.TrangThai:
            query = query.filter(Classroom.TrangThai == filters.TrangThai)

        return query
