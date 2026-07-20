from fastapi import APIRouter, Depends, status, HTTPException

from enums.user_role import UserRole
from services.UserService import UserService
from models.Users import User
from security import get_current_user, require_roles
from schemas.User import ChangePasswordRequest
from schemas.Student import StudentResponse
from schemas.Teacher import TeacherResponse
from schemas.api_response import success_response, error_response

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/me")
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    try:
        profile = await UserService.get_user_profile(current_user)
        if isinstance(profile, (StudentResponse, TeacherResponse)):
            return success_response(
                data=profile.model_dump(),
                message="Lấy thông tin người dùng thành công",
                status=200
            )
        return success_response(
            data=profile,
            message="Lấy thông tin người dùng thành công",
            status=200
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="PROFILE_ERROR"
        )


@router.put("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        result = await UserService.change_password(current_user, request)
        return success_response(
            data=result,
            message="Đổi mật khẩu thành công trên tất cả các site",
            status=200
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="PASSWORD_CHANGE_FAILED"
        )

