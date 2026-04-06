from django.urls import path
from . import views

urlpatterns = [
    path("add/", views.add_fuel, name="add-fuel"),
    path("admin/", views.admin_fuel_dashboard, name="admin-fuel-dashboard"),

    path("edit/<int:pk>/", views.edit_fuel, name="edit_fuel"),
    path("delete/<int:pk>/", views.delete_fuel, name="delete_fuel"),

    path("parking/", views.parking_entry, name="parking-entry"),
    path("parking/delete/<int:pk>/", views.delete_parking, name="delete_parking"),
]
