from rest_framework.routers import DefaultRouter

from split_the_bill import views


# NOTE: DRF has bug involve app's namespace and viewset's extra_actions,
# so we can't use app namespace for now
# Ref: https://github.com/encode/django-rest-framework/discussions/7816
# app_name = 'split_the_bill'

urlpatterns = [

]

router = DefaultRouter()
router.register('events', views.EventViewSet, basename='event')
router.register('groups', views.GroupViewSet, basename='group')
router.register('transactions', views.TransactionViewSet, basename='transaction')
router.register('event-invitations', views.EventInvitationViewSet, basename='event-invitation')

urlpatterns.extend(router.urls)
