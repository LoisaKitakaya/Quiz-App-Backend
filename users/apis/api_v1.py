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
    LoginUserSchema,
    UserInputSchema,
    UserUpdateSchema,
    UserPasswordResetSchema,
)

router = Router()

bearer = AuthBearer()


@router.post(
    "/new-user-signup",
    response=dict,
    description="Begin account creation process for new users",
)
def new_user_signup(request, data: UserInputSchema):
    try:
        if (
            User.objects.filter(email=data.email).exists()
            or User.objects.filter(username=data.username).exists()
        ):
            raise HttpError(
                400, "A user with the same email address or username already exists."
            )

        verification_token = new_user_jwt(
            first_name=data.first_name,
            last_name=data.last_name,
            username=data.username,
            email=data.email,
            password=data.password,
        )

        verification_url = f"{settings.BACKEND_URL}/api/v1/users/create-user?verification_token={verification_token}"

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
    except Exception as e:
        raise HttpError(500, str(e))


@router.post(
    "/complete-user-profile",
    response=dict,
    description="Complete account creation process for a user with a profile",
)
def complete_user_profile(request, data: UserInputSchema):
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
    "/create-user",
    description="Create a user after email verification",
)
def create__user(request, verification_token):
    verified_data = decode_jwt(verification_token)

    with transaction.atomic():
        user = User.objects.create(
            first_name=verified_data["first_name"],
            last_name=verified_data["last_name"],
            username=verified_data["username"],
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


@router.get(
    "/create-user-2",
    description="Create a user after email verification - for a user with an existing profile",
)
def create__user_two(request, verification_token):
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


@router.post(
    "/create-user-profile",
    response=UserSchema,
    description="Create a user profile at the beginning of a quiz",
)
def create_user_profile(request, data: UserInputSchema):
    user = User.objects.create(
        first_name=data.first_name,
        last_name=data.last_name,
        username=data.username,
        email=data.email,
    )

    return user


@router.get(
    "/me",
    auth=bearer,
    response=UserSchema,
    description="Retrieve a users own information",
)
def retrieve_user(request):
    try:
        assert isinstance(request.auth, User)

        username = request.auth

        return User.objects.get(username=username)
    except Exception as e:
        raise HttpError(500, str(e))


@router.put(
    "/me",
    response=UserSchema,
    auth=bearer,
    description="Update a users own information",
)
def update_user(request, data: UserUpdateSchema):
    try:
        assert isinstance(request.auth, User)

        username = request.auth

        user = User.objects.get(username=username)

        user.first_name = data.first_name if data.first_name else user.first_name
        user.last_name = data.last_name if data.last_name else user.last_name
        user.username = data.username if data.username else user.username
        user.email = data.email if data.email else user.email

        user.save()

        return user
    except Exception as e:
        raise HttpError(500, str(e))


@router.post(
    "/password-reset",
    response=dict,
    description="Password reset endpoint",
)
def password_reset(request, data: UserPasswordResetSchema):
    try:
        if not User.objects.filter(email=data.email).exists():
            raise HttpError(400, "The email address provided does not exists.")

        if not User.objects.get(email=data.email).is_active:
            raise HttpError(
                400, "You must be an active user to be able to reset password"
            )

        reset_token = password_reset_jwt(User.objects.get(email=data.email))

        reset_link = (
            f"{settings.BACKEND_URL}/auth/update_password?reset_token={reset_token}"
        )

        message = f"To reset your password, click the following link: {reset_link}."

        subject = "Password Reset"

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[data.email],
            fail_silently=True,
        )

        return {"message": f"A password reset email has been sent to {data.email}"}
    except Exception as e:
        raise HttpError(500, str(e))


@router.post(
    "/login",
    response=dict,
    description="Authenticate a user",
)
def login_user(request, data: LoginUserSchema):
    try:
        user = authenticate(username=data.username, password=data.password)

        if user is not None:
            find_user = User.objects.get(username=data.username)

            auth_token = login_jwt(find_user)

            return {
                "token": auth_token,
                "message": "Authentication successful",
            }

        else:
            raise HttpError(401, "Authentication failed: Wrong username or password")
    except Exception as e:
        raise HttpError(500, str(e))
