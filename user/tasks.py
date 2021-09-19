from celery import shared_task
from dateutil.parser import isoparse
from django.core.mail import send_mail
from django.template import loader
from django.utils import formats
from django.utils.translation import gettext_lazy as _


@shared_task
def send_email_reset_password_link_task(recipient, url):
    return send_email_reset_password_link(recipient, url)

def send_email_reset_password_link(recipient, url):
    date_joined = recipient['date_joined']
    date_joined_dt = isoparse(date_joined)
    date_joined_str = formats.localize(date_joined_dt)
    recipient['date_joined'] = date_joined_str

    context = {
        'url': url,
        'recipient': recipient,
        'app_name': _('Split the bill'),
    }
    title = loader.render_to_string('user/reset_password/email_title.txt', context)
    title = title.replace('\n', '')  # Title cannot have newline
    message = loader.render_to_string('user/reset_password/email_body.txt', context)
    html_message = loader.render_to_string('user/reset_password/email_body.html', context)
    send_mail(title, message, None, [recipient['email']], html_message=html_message)
