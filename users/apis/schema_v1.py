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


class ProfileInputSchema(Schema):
    first_name: str
    last_name: str
    username: str
    email: str


class CompleteProfileInputSchema(Schema):
    email: str
    password: str
    confirm_password: str
