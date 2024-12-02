from ninja.errors import HttpError
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.template.loader import render_to_string

TEMPLATE_CODE_NAME_LIST = [
    "PR",  # Password Reset (PR)
    "POWE",  # Property Owner Welcome Email (POWE)
    "TWE",  # Tenant Welcome Email (TWE)
    "AV",  # Account Verification (AV)
    "LB",  # Lease Billing Notification (LB)
    "PC",  # Payment Confirmation (PC)
    "GN",  # General Notification (GN)
    "POMR",  # Property Owner Maintenance Request (POMR)
    "TMR",  # Tenant Maintenance Request (TMR)
    "POLD",  # Property Owner Lease Document (POLD)
    "TLD",  # Tenant Lease Document (TLD)
]


def find_template(template_code_name: str) -> str:
    try:
        if template_code_name in TEMPLATE_CODE_NAME_LIST:
            if template_code_name == "PR":
                template_name = "temps/password_reset.html"
            elif template_code_name == "POWE":
                template_name = "temps/property_owner_welcome_email.html"
            elif template_code_name == "TWE":
                template_name = "temps/tenant_welcome_email.html"
            elif template_code_name == "AV":
                template_name = "temps/account_verification.html"
            elif template_code_name == "LB":
                template_name = "temps/lease_billing.html"
            elif template_code_name == "PC":
                template_name = "temps/payment_confirmation.html"
            elif template_code_name == "GN":
                template_name = "temps/general_notification.html"
            elif template_code_name == "POMR":
                template_name = "temps/property_owner_maintenance_request.html"
            elif template_code_name == "TMR":
                template_name = "temps/tenant_maintenance_request.html"
            elif template_code_name == "POLD":
                template_name = "temps/property_owner_lease_document.html"
            elif template_code_name == "TLD":
                template_name = "temps/tenant_lease_document.html"
        else:
            raise Exception(f"Unknown template code: {template_code_name}.")

        return template_name
    except Exception as e:
        raise HttpError(500, f"{str(e)}")


def send_email(
    mail_data: dict,
    subject: str,
    sender_email_address: str,
    receiver_email_address: str,
    template_code_name: str,
):
    template = find_template(template_code_name)

    html_content = render_to_string(template_name=template, context=mail_data)

    plain_content = strip_tags(html_content)

    send_mail(
        subject=subject,
        message=plain_content,
        from_email=sender_email_address,
        recipient_list=[
            receiver_email_address,
        ],
        html_message=html_content,
        fail_silently=True,
    )
