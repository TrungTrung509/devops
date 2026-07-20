from sqlalchemy.orm import Session
from models.Teachers import Teacher

class TeacherRepo:
    @staticmethod
    def get_by_maGV(db: Session, maGV: str) -> Teacher:
        return db.query(Teacher).filter(Teacher.MaGV == maGV).first()

    @staticmethod
    def get_by_MaGV(db: Session, maGV: str) -> Teacher:
        return TeacherRepo.get_by_maGV(db, maGV)

    @staticmethod
    def get_by_userId(db: Session, userId: str) -> Teacher:
        return db.query(Teacher).filter(Teacher.userId == userId).first()

    @staticmethod
    def get_by_coso(db: Session, maCoSo: str):
        return db.query(Teacher).filter(Teacher.MaCoSo == maCoSo.upper()).all()

    @staticmethod
    def get_by_khoa(db: Session, maKhoa: str):
        return db.query(Teacher).filter(Teacher.MaKhoa == maKhoa.upper()).all()

    @staticmethod
    def get_by_status(db: Session, status: str):
        return db.query(Teacher).filter(Teacher.TrangThai == status).all()

    @staticmethod
    def get_all(db: Session):
        return db.query(Teacher).all()

    @staticmethod
    def create(db: Session, teacher: Teacher) -> Teacher:
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        return teacher

    @staticmethod
    def update(db: Session, teacher: Teacher) -> Teacher:
        db.commit()
        db.refresh(teacher)
        return teacher

    @staticmethod
    def delete(db: Session, teacher: Teacher) -> bool:
        db.delete(teacher)
        db.commit()
        return True
