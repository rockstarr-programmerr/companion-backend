from django.urls import path
from . import google, facebook


urlpatterns = [
    path('google/authen/', google.callback_view, name='social_account_google_authen'),
    path('facebook/authen/', facebook.callback_view, name='social_account_facebook_authen'),
]
