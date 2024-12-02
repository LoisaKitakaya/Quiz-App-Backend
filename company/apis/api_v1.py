from ninja import Router
from django.conf import settings
from ninja.errors import HttpError
from .schema_v1 import ContactForm
from django.core.mail import send_mail

router = Router()


@router.post("contact-us", response=dict)
def contact_us(request, data: ContactForm):
    try:
        send_mail(
            subject="Contact From Client",
            message=f"Hello Alex! A client has made contact with you. The client's name is: {data.first_name} {data.last_name}. Email address: {data.email}. The client's message is: '{data.message}'. Make sure the client is responded to.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[
                "agiebner10@gmail.com",
                "kitakayaloisa@gmail.com",
            ],
            fail_silently=True,
        )

        return {"message": "Message submitted successfully"}
    except Exception as e:
        raise HttpError(500, str(e))
