from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from models.Courses import Course
from schemas.Course import CourseFilter


class CourseRepo:
    @staticmethod
    def base_query(db: Session) -> Query:
        return db.query(Course)

    @staticmethod
    def apply_filters(query: Query, filters: Optional[CourseFilter] = None) -> Query:
        if not filters:
            return query

        if filters.MaKhoa:
            query = query.filter(Course.MaKhoa == filters.MaKhoa.upper())
        if filters.TrangThai:
            query = query.filter(Course.TrangThai == filters.TrangThai)
        if filters.so_tin_chi_from is not None:
            query = query.filter(Course.SoTinChi >= filters.so_tin_chi_from)
        if filters.so_tin_chi_to is not None:
            query = query.filter(Course.SoTinChi <= filters.so_tin_chi_to)
        if filters.keyword:
            keyword = f"%{filters.keyword}%"
            query = query.filter(
                or_(
                    Course.MaHocPhan.ilike(keyword),
                    Course.TenHocPhan.ilike(keyword),
                    Course.MoTa.ilike(keyword),
                )
            )

        return query

    @staticmethod
    def get_by_id(db: Session, ma_hoc_phan: str) -> Optional[Course]:
        return db.query(Course).filter(Course.MaHocPhan == ma_hoc_phan).first()

    @staticmethod
    def create(db: Session, course: Course) -> Course:
        db.add(course)
        db.commit()
        db.refresh(course)
        return course
