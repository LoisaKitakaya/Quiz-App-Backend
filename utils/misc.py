from functools import wraps
from users.models import User
from datetime import datetime
from ninja.errors import HttpError


def check_if_is_staff(user: User):
    if not user.is_staff:
        raise HttpError(401, "Unauthorized.")


def get_client_ip(request):
    try:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[-1].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")

        return ip
    except Exception as e:
        raise Exception(str(e))


def check_user_role(username: str, required_role: str):
    try:
        user = User.objects.get(username=username)

        if user.role.lower() != required_role.lower():
            raise HttpError(401, f"User is not a {required_role}.")
    except User.DoesNotExist:
        raise HttpError(404, "User not found.")
    except Exception as e:
        raise HttpError(500, str(e))


def require_role(role):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            assert isinstance(request.auth, User)

            username = str(request.auth)

            check_user_role(username, role)

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def parse_html_date(date: str):
    try:
        if "T" in date:
            datetime_value = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
        else:
            datetime_value = datetime.strptime(date, "%Y-%m-%d")

        date_value = datetime_value.date()

        return {
            "datetime": datetime_value,
            "date": date_value,
        }
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}")
