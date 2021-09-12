from django.urls import path
from . import google


urlpatterns = [
    path('google/authen/', google.callback_view, name='social_account_google_authen'),
]
