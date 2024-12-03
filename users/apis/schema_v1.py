from users.models import User
from ninja import ModelSchema, Schema


class UserSchema(ModelSchema):
    class Meta:
        model = User
        exclude = [
            "groups",
            "password",
            "is_staff",
            "is_active",
            "last_login",
            "date_joined",
            "is_superuser",
            "user_permissions",
        ]


class UserInputSchema(Schema):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str
    confirm_password: str


class UserUpdateSchema(Schema):
    first_name: str
    last_name: str
    username: str
    email: str


class UserPasswordResetSchema(Schema):
    email: str


class LoginUserSchema(Schema):
    username: str
    password: str
