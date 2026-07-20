from sqlalchemy.orm import Session
from models.Students import Student

class StudentRepo:
    @staticmethod
    def get_by_maSV(db: Session, maSV: str) -> Student:
        return db.query(Student).filter(Student.MaSV == maSV).first()

    @staticmethod
    def get_by_MaSV(db: Session, maSV: str) -> Student:
        return StudentRepo.get_by_maSV(db, maSV)

    @staticmethod
    def get_by_userId(db: Session, userId: str) -> Student:
        return db.query(Student).filter(Student.userId == userId).first()

    @staticmethod
    def get_by_coso(db: Session, maCoSo: str):
        return db.query(Student).filter(Student.MaCoSo == maCoSo.upper()).all()

    @staticmethod
    def get_by_khoa(db: Session, maKhoa: str):
        return db.query(Student).filter(Student.MaKhoa == maKhoa.upper()).all()

    @staticmethod
    def get_by_status(db: Session, status: str):
        return db.query(Student).filter(Student.TrangThai == status).all()

    @staticmethod
    def get_all(db: Session):
        return db.query(Student).all()

    @staticmethod
    def create(db: Session, student: Student) -> Student:
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def update(db: Session, student: Student) -> Student:
        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def delete(db: Session, student: Student) -> bool:
        db.delete(student)
        db.commit()
        return True
