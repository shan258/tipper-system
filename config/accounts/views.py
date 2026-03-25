from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
import csv
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import DriverProfile, SalaryPercentageHistory
from django.contrib.auth.models import User
from fuel.models import FuelEntry, ParkingEntry
from datetime import date
from django.contrib import messages
from vehicles.models import Vehicle
import openpyxl
from django.contrib.auth import update_session_auth_hash
from .models import Notification
from trips.models import Trip
from .models import Profile
from trips.models import Salary
import json

@csrf_exempt
def driver_login_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user = authenticate(username=username, password=password)

    if not user:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    # ❌ BLOCK ADMIN LOGIN
    if user.is_staff:
        return JsonResponse({"error": "Admin not allowed"}, status=403)

    # ✅ CHECK DRIVER PROFILE
    try:
        profile = DriverProfile.objects.get(user=user)
    except DriverProfile.DoesNotExist:
        return JsonResponse({"error": "Driver profile not found"}, status=404)

    if not profile.is_active:
        return JsonResponse({"error": "Driver inactive"}, status=403)

    return JsonResponse({
        "success": True,
        "driver_id": profile.id,
        "username": user.username,
        "vehicle": profile.vehicle.vehicle_number if profile.vehicle else None,
    })

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # ✅ ADMIN
            if user.is_superuser or user.is_staff:
                return redirect("admin_dashboard")

            # ✅ DRIVER
            if hasattr(user, "driverprofile"):
                if not user.driverprofile.is_active:
                     return render(request, "accounts/login.html", {
                        "error": "Your account is inactive. Contact admin."
                    })
                return redirect("driver_dashboard")

            # ✅ FALLBACK
            return redirect("/")

        else:
            return render(request, "accounts/login.html", {
                "error": "Invalid username or password"
            })

    return render(request, "accounts/login.html")

def is_admin(user):
    return user.is_staff or user.is_superuser

@staff_member_required
def admin_dashboard(request):
    today = date.today()

    trips = Trip.objects.all().order_by('-start_time')
    parking_entries = ParkingEntry.objects.select_related("driver", "vehicle").order_by("-created_at")

    # 🔢 DASHBOARD COUNTS
    context = {
        "total_drivers": User.objects.filter(is_staff=False).count(),
        "total_vehicles": Vehicle.objects.count(),
        "total_trips": Trip.objects.count(),
        "open_trips": Trip.objects.filter(status="OPEN").count(),
        "fuel_entries": FuelEntry.objects.count(),
        "parking_entries": ParkingEntry.objects.count(),
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required
def driver_dashboard(request):
    if not hasattr(request.user, "driverprofile"):
        return redirect("admin_dashboard")
    return render(request, "accounts/driver_dashboard.html")


@login_required
@user_passes_test(is_admin)
def edit_driver_salary(request):
    drivers = DriverProfile.objects.select_related('user')

    if request.method == "POST":
        driver_id = request.POST.get("driver_id")
        new_percentage = request.POST.get("salary_percentage")

        profile = get_object_or_404(DriverProfile, id=driver_id)
        old_percentage = profile.salary_percentage

        if str(old_percentage) != new_percentage:
            SalaryPercentageHistory.objects.create(
                driver=profile.user,
                old_percentage=old_percentage,
                new_percentage=new_percentage,
                changed_by=request.user
            )
            profile.salary_percentage = new_percentage
            profile.save()

        return redirect("edit-driver-salary")

    return render(request, "admin/edit_driver_salary.html", {
        "drivers": drivers
    })

@login_required
@user_passes_test(is_admin)
def salary_history(request):
    history = SalaryPercentageHistory.objects.select_related(
        'driver', 'changed_by'
    ).order_by('-changed_at')

    return render(request, "admin/salary_history.html", {
        "history": history
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def driver_salary_view(request):
    from trips.models import Salary

    salaries = Salary.objects.select_related('driver', 'trip')

    return render(request, 'accounts/driver_salary_view.html', {
        'salaries': salaries
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def download_salary_excel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="driver_salary.csv"'

    writer = csv.writer(response)
    writer.writerow(['Driver', 'Trip', 'Amount'])

    # example logic – adjust if needed
    from trips.models import Salary
    for s in Salary.objects.all():
        writer.writerow([s.driver.username, s.trip.id, s.amount])

    return response

@login_required
@user_passes_test(is_admin)
def add_driver(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        phone = request.POST.get("phone")
        license_no = request.POST.get("license")
        vehicle_number = request.POST.get("vehicle")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("add_driver")

        user = User.objects.create_user(
            username=username,
            password=password
        )

        profile = user.driverprofile
        profile.phone = phone
        profile.license_no = license_no
        profile.is_active = True

        # ✅ MANUAL VEHICLE ASSIGN
        if vehicle_number:
            vehicle_number = vehicle_number.upper().strip()

            vehicle, created = Vehicle.objects.get_or_create(
                vehicle_number=vehicle_number
            )

            profile.vehicle = vehicle

        profile.save()

        messages.success(request, "Driver added successfully")
        return redirect("driver_list")

    return render(request, "accounts/add_driver.html")
@login_required
@user_passes_test(is_admin)
def driver_list(request):
    drivers = DriverProfile.objects.select_related(
        "user", "vehicle"
    ).filter(
        user__is_staff=False,
        user__is_superuser=False
    )

    return render(
        request,
        "accounts/driver_list.html",
        {"drivers": drivers}
    )

@login_required
@user_passes_test(is_admin)
def edit_driver(request, driver_id):
    profile = get_object_or_404(DriverProfile, id=driver_id)
    vehicles = Vehicle.objects.all()

    if request.method == "POST":
        profile.phone = request.POST.get("phone")
        profile.license_no = request.POST.get("license_no")
        profile.is_active = request.POST.get("is_active") == "on"

        vehicle_number = request.POST.get("vehicle_number")

        if vehicle_number:
            vehicle_number = vehicle_number.upper().strip()
            vehicle, _ = Vehicle.objects.get_or_create(
                vehicle_number=vehicle_number
            )
            profile.vehicle = vehicle
        else:
            profile.vehicle = None

        profile.save()
        messages.success(request, "Driver updated successfully")
        return redirect("driver_list")

    return render(request, "accounts/edit_driver.html", {
        "driver": profile,
        "vehicles": vehicles
    })

@login_required
@user_passes_test(is_admin)
def activate_driver(request, driver_id):
    driver = get_object_or_404(DriverProfile, id=driver_id)
    driver.is_active = True
    driver.save()

    messages.success(request, "Driver activated")
    return redirect("driver_list")

@login_required
@user_passes_test(is_admin)
def deactivate_driver(request, driver_id):
    driver = get_object_or_404(DriverProfile, id=driver_id)
    driver.is_active = False
    driver.save()

    messages.warning(request, "Driver deactivated")
    return redirect("driver_list")

@login_required
@user_passes_test(is_admin)
def delete_driver(request, driver_id):
    driver = get_object_or_404(DriverProfile, id=driver_id)

    with transaction.atomic():   # ✅ now Python knows transaction
        user = driver.user
        driver.delete()
        user.delete()

    messages.success(request, "Driver deleted permanently")
    return redirect("driver_list")

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_profile(request):
    user = request.user

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # 1️⃣ Update username
        if username:
            user.username = username

        # 2️⃣ Validate password
        if password:
            if password != confirm_password:
                messages.error(request, "Passwords do not match")
                return redirect("admin_profile")

            user.set_password(password)
            user.save()

            # 🔐 Important: logout after password change
            messages.success(
                request,
                "Profile updated successfully. Please login again."
            )
            return redirect("login")

        user.save()
        messages.success(request, "Username updated successfully")

    return render(request, "accounts/admin_profile.html", {
        "user": user
    })

@login_required
def driver_profile(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")

    profile = request.user.driverprofile

    return render(request, "accounts/driver_profile.html", {
        "profile": profile
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def driver_trip_summary(request, driver_id):
    driver = get_object_or_404(DriverProfile, id=driver_id)

    trips = Trip.objects.filter(
        driver=driver.user
    ).select_related("vehicle").order_by("-start_time")

    return render(request, "accounts/driver_trip_summary.html", {
        "driver": driver,
        "trips": trips
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def download_driver_trip_excel(request, driver_id):
    driver = DriverProfile.objects.get(id=driver_id)
    trips = Trip.objects.filter(driver=driver.user).order_by("start_time")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Daily Trip Details"

    headers = [
        "SL.NO", "DATE", "COMPANY", "DRIVER NAME", "VEHICLE NUMBER",
        "MATERIAL", "DO / TICKET NO", "NET WEIGHT",
        "PICKUP-LOCATION", "TIME IN",
        "DROP-LOCATION", "TIME OUT",
        "DROP COUNT", "Salary"
    ]

    ws.append(headers)

    total_salary = 0
    for idx, trip in enumerate(trips, start=1):
        total_salary += trip.salary or 0

        ws.append([
            idx,
            trip.start_time.date(),
            trip.company,
            driver.user.username,
            trip.vehicle.vehicle_number,
            trip.material,
            trip.ticket_no,
            trip.net_weight,
            trip.start_location,
            trip.start_time.strftime("%I:%M %p"),
            trip.end_location,
            trip.end_time.strftime("%I:%M %p") if trip.end_time else "",
            trip.drop_count,
            trip.salary
        ])

    ws.append([])
    ws.append(["", "", "", "", "", "", "", "", "", "", "", "TOTAL", "", total_salary])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{driver.user.username}_trip_summary.xlsx"'
    )

    wb.save(response)
    return response
    
@staff_member_required
def admin_parking_list(request):
    parking_entries = ParkingEntry.objects.select_related(
        "driver", "vehicle"
    ).order_by("-created_at")

    return render(
        request,
        "accounts/admin_parking_list.html",
        {
            "parking_entries": parking_entries
        }
    )

def mark_notification_read(request, id):
    notification = get_object_or_404(
        Notification,
        id=id,
        recipient=request.user
    )
    notification.is_read = True
    notification.save()

    return redirect(notification.link or "admin_dashboard")