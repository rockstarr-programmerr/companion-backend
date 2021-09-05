from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from companion.utils.url import update_url_params

token_generator = PasswordResetTokenGenerator()


def send_email(user, deeplink):
    url = get_link(user, deeplink)
    # TODO
    message = f"Yo check this out: {url}"
    send_mail('Hello!', message, None, [user.email])


def get_link(user, deeplink):
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    url = update_url_params(deeplink, {'token': token, 'uid': uid})
    return url
