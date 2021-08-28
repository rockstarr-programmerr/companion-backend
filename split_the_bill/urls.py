from django.urls import path
from rest_framework.routers import DefaultRouter

from split_the_bill import views


app_name = 'split_the_bill'

urlpatterns = [

]

router = DefaultRouter()
router.register('trips', views.TripViewSet, basename='trip')
router.register('groups', views.GroupViewSet, basename='group')

urlpatterns.extend(router.urls)
