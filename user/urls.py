from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter

from . import views


# NOTE: DRF has bug involve app's namespace and viewset's extra_actions,
# so we can't use app namespace for now
# Ref: https://github.com/encode/django-rest-framework/discussions/7816
# app_name = 'user'

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/info/', views.MyInfoViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'update'}), name='user-my-info')
]

router = DefaultRouter()
router.register('me/event-invitations', views.UserEventInvitationViewSet, basename='user-my-event-invitation')
router.register('', views.UserViewSet, basename='user')
urlpatterns.extend(router.urls)
