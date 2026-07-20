from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from configs.db import get_db
from enums.user_role import UserRole
from schemas.Branch import BranchCreate, BranchUpdate
from schemas.api_response import success_response, error_response
from services.BranchService import BranchService
from models.Users import User
from security import get_current_user, get_current_user_db, require_roles

router = APIRouter(
    prefix="/branches",
    tags=["Branches"]
)


@router.get("/")
async def get_all_branches(
    db: Session = Depends(get_current_user_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách tất cả cơ sở (Branch - tên cũ)"""
    try:
        branches = await BranchService.get_all_branches(db)
        return success_response(
            data=[b for b in branches],
            message=f"Lấy danh sách chi nhánh thành công (tổng: {len(branches)})",
            status=200
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_BRANCHES_FAILED"
        )


@router.get("/{branch_id}")
async def get_branch(
    branch_id: str,
    db: Session = Depends(get_current_user_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy thông tin cơ sở theo ID"""
    try:
        branch = await BranchService.get_branch_by_id(db, branch_id)
        return success_response(
            data=branch,
            message=f"Lấy thông tin chi nhánh '{branch_id}' thành công",
            status=200
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="BRANCH_NOT_FOUND"
        )


@router.post("/")
async def create_branch(
    branch_in: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.Admin))
):
    """Tạo mới cơ sở (Admin only)"""
    try:
        branch = await BranchService.create_branch(db, branch_in, current_user)
        return success_response(
            data=branch,
            message=f"Tạo chi nhánh '{branch_in.MaCoSo}' thành công",
            status=201
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CREATE_BRANCH_FAILED"
        )


@router.put("/{branch_id}")
async def update_branch(
    branch_id: str,
    branch_in: BranchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.Admin))
):
    """Cập nhật thông tin cơ sở (Admin only)"""
    try:
        branch = await BranchService.update_branch(db, branch_id, branch_in, current_user)
        return success_response(
            data=branch,
            message=f"Cập nhật chi nhánh '{branch_id}' thành công",
            status=200
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_BRANCH_FAILED"
        )

@router.delete("/{branch_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.Admin))
):
    """Xóa cơ sở (Admin only)"""
    try:
        await BranchService.delete_branch(db, branch_id, current_user)
        return success_response(
            data=None,
            message=f"Xóa chi nhánh '{branch_id}' thành công",
            status=status.HTTP_204_NO_CONTENT
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="DELETE_BRANCH_FAILED"
        )
