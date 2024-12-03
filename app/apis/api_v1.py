from ninja import NinjaAPI
from http import HTTPStatus
from django.core.exceptions import (
    FieldError,
    ValidationError,
    PermissionDenied,
    ObjectDoesNotExist,
)
from ninja.errors import ValidationError as NinjaValidationError

api_v1 = NinjaAPI(urls_namespace="rems_api_v1", version="1.0.0")

"""
NOTE: Registration of endpoints here 👇
"""

from company.apis.api_v1 import router as company_router
from quiz.apis.api_v1 import router as quiz_router
from users.apis.api_v1 import router as users_router

api_v1.add_router("company/", company_router, tags=["Company"])
api_v1.add_router("quiz/", quiz_router, tags=["Quiz"])
api_v1.add_router("users/", users_router, tags=["Users"])

"""
NOTE: Registration of endpoints here 👆
"""


@api_v1.exception_handler(ObjectDoesNotExist)
def handle_object_does_not_exist(request, exc):
    return api_v1.create_response(
        request,
        {"message": "ObjectDoesNotExist", "detail": str(exc)},
        status=HTTPStatus.NOT_FOUND,
    )


@api_v1.exception_handler(PermissionDenied)
def handle_permission_error(request, exc: PermissionDenied):
    return api_v1.create_response(
        request,
        {
            "message": "PermissionDenied",
            "detail": "You don't have the permission to access this resource.",
        },
        status=HTTPStatus.FORBIDDEN,
    )


@api_v1.exception_handler(NinjaValidationError)
def handle_ninja_validation_error(request, exc: NinjaValidationError):
    mapped_msg = {error["loc"][-1]: error["msg"] for error in exc.errors}
    return api_v1.create_response(
        request,
        data={"message": "NinjaValidationError", "detail": mapped_msg},
        status=HTTPStatus.BAD_REQUEST,
    )


@api_v1.exception_handler(ValidationError)
def handle_validation_error(request, exc: ValidationError):
    status = HTTPStatus.BAD_REQUEST
    for field, errors in exc.error_dict.items():  # type: ignore
        for error in errors:
            if error.code in ["unique", "unique_together"]:
                status = HTTPStatus.CONFLICT
    return api_v1.create_response(
        request,
        data={"message": "ValidationError", "detail": exc.message_dict},
        status=status,
    )


@api_v1.exception_handler(FieldError)
def handle_field_error(request, exc: FieldError):
    return api_v1.create_response(
        request,
        data={"message": "FieldError", "detail": str(exc)},
        status=HTTPStatus.BAD_REQUEST,
    )
