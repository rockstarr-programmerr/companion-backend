from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from ._utils import MobileAppCallbackView


class MobileAppGoogleAdapter(GoogleOAuth2Adapter):
    pass


callback_view = MobileAppCallbackView.adapter_view(MobileAppGoogleAdapter)
