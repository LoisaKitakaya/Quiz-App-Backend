from ninja import Schema


class ContactForm(Schema):
    first_name: str
    last_name: str
    email: str
    message: str
