from sqlalchemy.orm import Session
from models.Branches import Branch

class BranchRepo:
    @staticmethod
    def get_by_id(db: Session, MaCoSo: str) -> Branch:
        return db.query(Branch).filter(Branch.MaCoSo == MaCoSo).first()

    @staticmethod
    # Viet
    def get_by_MaCoSo(db: Session, ma_co_so: str) -> Branch:
        return db.query(Branch).filter(Branch.MaCoSo == ma_co_so.upper()).first()

    @staticmethod
    def create(db: Session, branch: Branch) -> Branch:
        db.add(branch)
        db.commit()
        db.refresh(branch)
        return branch

    @staticmethod
    def update(db: Session, branch: Branch) -> Branch:
        db.commit()
        db.refresh(branch)
        return branch
