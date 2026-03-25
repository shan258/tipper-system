from django.urls import path
from .views import login_view, edit_driver_salary, salary_history, driver_dashboard, driver_salary_view, driver_login_api
from . import views
from django.urls import path, include

urlpatterns = [
    path("login/", login_view, name="login"),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('driver-dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path("salary/edit/", edit_driver_salary, name="edit-driver-salary"),
    path("salary/history/", salary_history, name="salary-history"),
    path("driver-dashboard/", driver_dashboard, name="driver-dashboard"),
    path('salary/', views.driver_salary_view, name='driver-salary-view'),
    path('salary/', views.driver_salary_view, name='driver-salary-view'),
    path('salary/download/', views.download_salary_excel, name='download-salary'),
    path('admin-dashboard/add-driver/', views.add_driver, name='add_driver'),
    path("admin-dashboard/drivers/", views.driver_list, name="driver_list"),
    path("drivers/edit/<int:driver_id>/", views.edit_driver, name="edit_driver"),
    path("drivers/activate/<int:driver_id>/", views.activate_driver, name="activate_driver"),
    path("drivers/deactivate/<int:driver_id>/", views.deactivate_driver, name="deactivate_driver"),
    path("drivers/delete/<int:driver_id>/", views.delete_driver, name="delete_driver"),
    path("profile/admin/", views.admin_profile, name="admin_profile"),
    path("profile/driver/", views.driver_profile, name="driver_profile"),
    path(
        "drivers/<int:driver_id>/trips/",
        views.driver_trip_summary,
        name="driver_trip_summary"
    ),
    path(
    "drivers/<int:driver_id>/download/",
    views.download_driver_trip_excel,
    name="download_driver_trip_excel"
    ),
    path("parking/", views.admin_parking_list, name="admin_parking_list"),
    path(
    "notifications/read/<int:id>/",
    views.mark_notification_read,
    name="mark_notification_read"
    ),
    path("api/driver/login/", driver_login_api, name="driver_login_api"),
    path("api/", include("accounts.api_urls")),

]