import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.Users import User
from models.Branches import Branch
from schemas.Branch import BranchCreate, BranchUpdate
from repositories.BranchRepo import BranchRepo
from enums.user_role import UserRole

class BranchService:
    @staticmethod
    def get_by_MaCoSo(db: Session, MaCoSo: str) -> Branch:
        branch = BranchRepo.get_by_MaCoSo(db, MaCoSo)
        if not branch:
            raise HTTPException(status_code=404, detail="Branch not found")
        return branch

    @staticmethod
    async def create_branch(db: Session, branch_in: BranchCreate, current_user: User) -> Branch:
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can create branches"
            )

        if BranchRepo.get_by_MaCoSo(db, branch_in.MaCoSo):
            raise HTTPException(status_code=400, detail="Branch with this MaCoSo already exists")
        db_branch = Branch(
            # Viet
            MaCoSo=branch_in.MaCoSo.upper(),
            TenCoSo=branch_in.TenCoSo,
            DiaChi=branch_in.DiaChi,
            SoDienThoai=branch_in.SoDienThoai,
            Email=branch_in.Email,
            NgayThanhLap=branch_in.NgayThanhLap,
            TrangThai=branch_in.TrangThai
        )
        return BranchRepo.create(db, db_branch)

    @staticmethod
    async def get_all_branches(db: Session):
        return db.query(Branch).all()

    @staticmethod
    async def get_branch_by_id(db: Session, branch_id: str):
        branch = BranchRepo.get_by_id(db, branch_id)
        if not branch:
            raise HTTPException(status_code=404, detail="Branch not found")
        return branch

    @staticmethod
    async def update_branch(db: Session, branch_id: str, branch_in: BranchUpdate, current_user: User):
        if current_user.role != UserRole.Admin:
            raise HTTPException(status_code=403, detail="Only Admin can update branches")

        branch = BranchRepo.get_by_id(db, branch_id)
        if not branch:
            raise HTTPException(status_code=404, detail="Branch not found")

        update_data = branch_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'MaCoSo' and value:
                value = value.upper()
            if hasattr(branch, field):
                setattr(branch, field, value)

        return BranchRepo.update(db, branch)
    @staticmethod
    async def delete_branch(db: Session, branch_id: str, current_user: User):
        if current_user.role != UserRole.Admin:
            raise HTTPException(status_code=403, detail="Only Admin can delete branches")

        branch = BranchRepo.get_by_id(db, branch_id)
        if not branch:
            raise HTTPException(status_code=404, detail="Branch not found")

        db.delete(branch)
        db.commit()
        return True