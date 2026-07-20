from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "http://localhost:3000",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
}


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {"msg": "Validation error"}
    safe_errors = []

    for err in errors:
        err = dict(err)
        err.pop("input", None)
        safe_errors.append(err)

    return JSONResponse(
        status_code=422,
        content={
            "status": 422,
            "success": False,
            "message": f"Validation error: {first_error.get('msg', 'Invalid input')}",
            "data": None,
            "errorr": safe_errors,
        },
        headers=CORS_HEADERS,
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "success": False,
            "message": exc.detail,
            "data": None,
            "errorr": {
                "code": "HTTP_ERROR",
                "details": exc.detail,
            },
        },
        headers=CORS_HEADERS,
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "success": False,
            "message": "Loi co so du lieu",
            "data": None,
            "errorr": {
                "code": "DATABASE_ERROR",
                "details": str(exc.__class__.__name__),
            },
        },
        headers=CORS_HEADERS,
    )


async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "success": False,
            "message": "Loi he thong noi bo",
            "data": None,
            "errorr": {
                "code": "INTERNAL_ERROR",
                "details": str(exc.__class__.__name__),
            },
        },
        headers=CORS_HEADERS,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
