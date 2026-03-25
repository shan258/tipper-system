from django.urls import path
from . import views

app_name = "trips"

urlpatterns = [
    path("open/", views.open_trip, name="open_trip"),
    path("close/", views.close_trip, name="close_trip"),

    # Admin – driver trip summary
    path(
        "driver/<int:driver_id>/summary/",
        views.admin_driver_trip_summary,
        name="admin_driver_trip_summary",
    ),

    # Admin – download trip summary Excel
    path(
        "driver/<int:driver_id>/download-excel/",
        views.download_driver_trip_excel,
        name="download_driver_trip_excel",
    ),

    # Driver – own trip summary
    path(
        "drivers/<int:driver_id>/trips/",
        views.driver_trip_summary,
        name="driver_trip_summary",
    ),

    path("trip/<int:trip_id>/edit/", views.edit_trip, name="edit_trip"),
    path("trip/<int:trip_id>/delete/", views.delete_trip, name="delete_trip"),
]
