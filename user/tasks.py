from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_email_reset_password_link(email, url):
    message = f"Yo check this out: {url}"
    send_mail('Hello internet!', message, None, [email])
