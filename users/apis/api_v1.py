from ninja import Router
from users.models import User
from django.conf import settings
from django.db import transaction
from ninja.errors import HttpError
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from utils.auth import (
    AuthBearer,
    login_jwt,
    decode_jwt,
    new_user_jwt,
    password_reset_jwt,
)
from .schema_v1 import (
    UserSchema,
    ProfileInputSchema,
    CompleteProfileInputSchema,
)

router = Router()

bearer = AuthBearer()


@router.post(
    "/create-user-profile",
    response=UserSchema,
    description="Create a user profile at the end of a quiz",
)
def create_user_profile(request, data: ProfileInputSchema):
    user = User.objects.create(
        first_name=data.first_name,
        last_name=data.last_name,
        username=data.username,
        email=data.email,
    )

    return user


@router.post(
    "/complete-user-profile",
    response=dict,
    description="Complete account creation process for a user with a profile",
)
def complete_user_profile(request, data: CompleteProfileInputSchema):
    try:
        user = User.objects.get(email=data.email)

        assert User.objects.filter(email=data.email).exists()

        if len(data.password) <= 8:
            raise HttpError(
                400, "Password is too short. Must have minimum of 8 characters!"
            )

        if data.password != data.confirm_password:
            raise HttpError(400, "Passwords provided did not match!")

        verification_token = new_user_jwt(
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
            password=data.password,
        )

        verification_url = f"{settings.BACKEND_URL}/api/v1/users/create-user-2?verification_token={verification_token}"

        message = (
            f"To verify your account, click the following link: {verification_url}."
        )

        subject = "Account Verification"

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[data.email],
            fail_silently=True,
        )

        return {"message": f"A verification email has been sent to {data.email}"}
    except AssertionError:
        raise HttpError(400, "You should have a profile created for this email")
    except Exception as e:
        raise HttpError(500, str(e))


@router.get(
    "/create-user-with-password",
    description="Create a user after email verification - for a user with an existing profile",
)
def create_user_with_password(request, verification_token):
    verified_data = decode_jwt(verification_token)

    with transaction.atomic():
        user = User.objects.get(
            email=verified_data["email"],
        )

        user.set_password(verified_data["password"])
        user.save()

        message = f"Dear {user.first_name}, welcome to the app."

        subject = "New Account"

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=True,
        )

    return redirect(f"{settings.FRONTEND_URL}/auth/sign-in?verified=true")
