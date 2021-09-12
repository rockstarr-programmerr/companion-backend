from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from ._utils import MobileAppCallbackView


class MobileAppFacebookAdapter(FacebookOAuth2Adapter):
    pass


callback_view = MobileAppCallbackView.adapter_view(MobileAppFacebookAdapter)
