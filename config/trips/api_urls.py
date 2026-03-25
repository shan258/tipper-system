from django.urls import path
from .api_views import open_trip_api, close_trip_api

urlpatterns = [
    path("trip/open/", open_trip_api),
    path("trip/close/", close_trip_api),
]
