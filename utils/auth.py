import jwt
from users.models import User
from django.conf import settings
from ninja.security import HttpBearer
from datetime import datetime, timedelta


def login_jwt(user: User) -> str | None:
    try:
        expiry_date = datetime.now() + timedelta(days=3)

        token = jwt.encode(
            {
                "id": str(user.pk),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_staff": user.is_staff,
                "expires": expiry_date.timestamp(),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        return token
    except Exception as e:
        raise Exception(str(e))


def new_user_jwt(first_name, last_name, username, email, phone, password) -> str | None:
    try:
        token = jwt.encode(
            {
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "email": email,
                "phone": phone,
                "password": password,
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        return token
    except Exception as e:
        raise Exception(str(e))


def password_reset_jwt(user: User) -> str | None:
    try:
        expiry_date = datetime.now() + timedelta(hours=1)

        token = jwt.encode(
            {
                "id": user.pk,
                "email": user.email,
                "is_active": user.is_active,
                "expires": expiry_date.timestamp(),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        return token
    except Exception as e:
        raise Exception(str(e))


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.DecodeError as e:
        raise Exception(f"Token is invalid: {str(e)}")
    except Exception as e:
        raise Exception(str(e))


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        if token:
            try:
                res = decode_jwt(token)

                if res and "username" in res:
                    return User.objects.get(username=res["username"])  # type: ignore
            except User.DoesNotExist:
                pass
