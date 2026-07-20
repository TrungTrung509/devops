from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

T = TypeVar("T")


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "http://localhost:3000",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
}


class APIResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)

    status: int = 200
    success: bool = True
    message: str = "Thành công"
    data: Optional[T] = None
    errorr: Optional[Any] = None


class ErrorDetail(BaseModel):
    code: Optional[str] = None
    details: Optional[str] = None
    field: Optional[str] = None


def success_response(data: Any = None, message: str = "Success", status: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=jsonable_encoder({
            "status": status,
            "success": True,
            "message": message,
            "data": data,
            "errorr": None
        }),
        headers=CORS_HEADERS,
    )


def error_response(
    message: str,
    status: int = 400,
    error_code: str = "ERROR",
    data: Any = None,
    details: Optional[str] = None,
    field: Optional[str] = None
) -> JSONResponse:
    error_data = {
        "code": error_code,
        "details": details or message,
        "field": field
    }

    return JSONResponse(
        status_code=status,
        content=jsonable_encoder({
            "status": status,
            "success": False,
            "message": message,
            "data": data,
            "errorr": error_data
        }),
        headers=CORS_HEADERS,
    )


def not_found_response(
    resource: str = "Tài nguyên",
    identifier: Optional[str] = None
) -> JSONResponse:
    msg = f"{resource} không tồn tại"
    if identifier:
        msg = f"{resource} với mã '{identifier}' không tồn tại"

    return error_response(
        message=msg,
        status=404,
        error_code="NOT_FOUND",
        details=msg
    )


def validation_error_response(
    message: str,
    field: Optional[str] = None,
    details: Optional[str] = None
) -> JSONResponse:
    return error_response(
        message=message,
        status=422,
        error_code="VALIDATION_ERROR",
        details=details or message,
        field=field
    )


def unauthorized_response(
    message: str = "Không có quyền truy cập",
    details: Optional[str] = None
) -> JSONResponse:
    return error_response(
        message=message,
        status=401,
        error_code="UNAUTHORIZED",
        details=details or message
    )


def forbidden_response(
    message: str = "Không có quyền thực hiện thao tác này",
    details: Optional[str] = None
) -> JSONResponse:
    return error_response(
        message=message,
        status=403,
        error_code="FORBIDDEN",
        details=details or message
    )


def server_error_response(
    message: str = "Lỗi server nội bộ",
    details: Optional[str] = None
) -> JSONResponse:
    return error_response(
        message=message,
        status=500,
        error_code="INTERNAL_SERVER_ERROR",
        details=details or message
    )


def created_response(
    data: Any,
    message: str = "Tạo mới thành công"
) -> JSONResponse:
    return success_response(
        data=data,
        message=message,
        status=201
    )


def deleted_response(
    message: str = "Xóa thành công"
) -> JSONResponse:
    return success_response(
        data=None,
        message=message,
        status=200
    )
