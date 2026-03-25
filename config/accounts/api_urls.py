from django.urls import path
from .api_views import driver_login

urlpatterns = [
     path("driver/login/", driver_login, name="driver_login"),
]
