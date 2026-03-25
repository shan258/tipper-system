from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from accounts.models import DriverProfile
from openpyxl import Workbook
from django.http import HttpResponse
from django.db.models import Sum
from django.contrib import messages
from datetime import datetime
from .models import Trip
from decimal import Decimal
from vehicles.models import Vehicle
import openpyxl
from accounts.utils import notify_admin
from django.urls import reverse



@login_required
@user_passes_test(lambda u: not u.is_staff)
def open_trip(request):
    driver_profile = get_object_or_404(DriverProfile, user=request.user)

    if not driver_profile.vehicle:
        messages.error(request, "No vehicle assigned. Contact admin.")
        return redirect("driver_dashboard")

    if request.method == "POST":

        # ✅ 1. CREATE trip AND STORE it
        trip = Trip.objects.create(
            driver=request.user,
            vehicle=driver_profile.vehicle,
            start_location=request.POST.get("start_location"),
            start_meter_reading=request.POST.get("start_meter_reading"),
            start_meter_image=request.FILES.get("start_meter_image"),
            status="OPEN"
        )

        # ✅ 2. SEND notification with VALID link
        notify_admin(
            message=f"🚛 Trip opened by {request.user.username}",
            link=reverse(
                "driver_trip_summary",
                kwargs={"driver_id": trip.driver.id}
            )
        )

    if Trip.objects.filter(driver=request.user, status="OPEN").exists():
        messages.error(request, "You already have an open trip.")
        return redirect("driver_dashboard")


        messages.success(request, "Trip opened successfully")
        return redirect("driver_dashboard")

    return render(request, "trips/open_trip.html", {
        "vehicle": driver_profile.vehicle
    })


# =========================
# DRIVER – CLOSE TRIP
# =========================
@login_required
@user_passes_test(lambda u: not u.is_staff)
def close_trip(request):
    trip = Trip.objects.filter(
        driver=request.user,
        status="OPEN"
    ).order_by("-start_time").first()

    if not trip:
        messages.error(request, "No open trip found")
        return redirect("driver_dashboard")

    if request.method == "POST":
        trip.end_location = request.POST.get("end_location")
        trip.ticket_no = request.POST.get("ticket_no")
        trip.material = request.POST.get("material")
        trip.net_weight = request.POST.get("net_weight") or 0
        trip.drop_count = request.POST.get("drop_count") or 0
        trip.end_meter_reading = int(request.POST.get("end_meter_reading"))
        trip.end_meter_image = request.FILES.get("end_meter_image")
        trip.status = "CLOSED"
        trip.end_time = timezone.now()
        trip.save()

        notify_admin(
            message=f"✅ Trip closed by {request.user.username}",
            link=reverse(
                "driver_trip_summary",
                kwargs={"driver_id": trip.driver.id}
            )
        )

        messages.success(request, "Trip closed successfully")
        return redirect("driver_dashboard")

    return render(request, "trips/close_trip.html", {"trip": trip})


# =========================
# ADMIN – DRIVER TRIP SUMMARY
# =========================
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_driver_trip_summary(request, driver_id):
    driver = get_object_or_404(DriverProfile, id=driver_id)

    trips = Trip.objects.filter(
        driver=driver.user
    ).select_related("vehicle").order_by("-start_time")

    # 📅 Date range filter
    start_date, end_date = get_date_range(request)
    if start_date and end_date:
        trips = trips.filter(start_time__date__range=[start_date, end_date])

    return render(request, "accounts/driver_trip_summary.html", {
    "driver": driver,
    "trips": trips,
    "start_date": start_date,
    "end_date": end_date,
})



# =========================
# ADMIN – SALARY SUMMARY
# =========================
@staff_member_required
def driver_salary_summary(request):
    trips = Trip.objects.filter(status="CLOSED").select_related("driver")

    # 📅 Date range filter
    start_date, end_date = get_date_range(request)
    if start_date and end_date:
           trips = trips.filter(start_time__date__range=[start_date, end_date])

    for trip in trips:
        profile, _ = DriverProfile.objects.get_or_create(
            user=trip.driver,
            defaults={"salary_percentage": 20}
        )

        salary = (Decimal(trip.salary) * profile.salary_percentage) / 100

        summary.setdefault(trip.driver, {
            "percentage": profile.salary_percentage,
            "total_salary": Decimal(0),
            "trips": []
        })

        summary[trip.driver]["total_salary"] += salary
        summary[trip.driver]["trips"].append(trip)

    return render(request, "admin/driver_salary_summary.html", {
        "summary": summary,
        "start_date": start_date,
        "end_date": end_date,
    })


# =========================
# ADMIN – EXCEL DOWNLOAD
# =========================
@login_required
@user_passes_test(lambda u: u.is_staff)
def download_driver_trip_excel(request, driver_id):
    driver = get_object_or_404(DriverProfile, id=driver_id)

    trips = Trip.objects.filter(
        driver=driver.user
    ).select_related("vehicle").order_by("start_time")

    # 📅 DATE RANGE FILTER (SAFE)
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            trips = trips.filter(start_time__date__range=[start_date, end_date])
        except ValueError:
            pass  # ignore invalid dates safely

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Daily Trip Details"

    headers = [
        "SL.NO", "DATE", "COMPANY", "DRIVER NAME", "VEHICLE NUMBER",
        "MATERIAL", "DO / TICKET NO", "NET WEIGHT",
        "PICKUP LOCATION", "TIME IN",
        "DROP LOCATION", "TIME OUT",
        "DROP COUNT", "SALARY"
    ]
    ws.append(headers)

    total_salary = 0
    for idx, trip in enumerate(trips, start=1):
        salary = trip.salary or 0
        total_salary += salary

        ws.append([
            idx,
            trip.start_time.date() if trip.start_time else "",
            getattr(trip, "company", ""),   # SAFE
            driver.user.username,
            trip.vehicle.vehicle_number if trip.vehicle else "",
            trip.material,
            trip.ticket_no,
            trip.net_weight,
            trip.start_location,
            trip.start_time.strftime("%I:%M %p") if trip.start_time else "",
            trip.end_location or "",
            trip.end_time.strftime("%I:%M %p") if trip.end_time else "",
            trip.drop_count,
            salary,
        ])

    # TOTAL ROW
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

@login_required
@user_passes_test(lambda u: not u.is_staff)
def driver_salary_view(request):
    salaries = []  # query driver salary here
    return render(request, "driver/salary_view.html", {"salaries": salaries})

@login_required
def driver_trip_summary(request, driver_id):
    if request.user.id != driver_id:
        return redirect("driver_dashboard")

    trips = Trip.objects.filter(driver_id=driver_id).order_by("-start_time")

    start_date, end_date = get_date_range(request)
    if start_date and end_date:
        trips = trips.filter(start_time__date__range=[start_date, end_date])

    return render(
        request,
        "trips/driver_trip_summary.html",
        {
            "trips": trips,
            "start_date": start_date,
            "end_date": end_date,
            "driver": request.user.driverprofile,
        }
    )


@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)

    if request.method == "POST":
        trip.start_location = request.POST.get("start_location")
        trip.end_location = request.POST.get("end_location")
        trip.start_meter_reading = request.POST.get("start_meter_reading")
        trip.end_meter_reading = request.POST.get("end_meter_reading")
        trip.save()

        messages.success(request, "Trip updated successfully")
        return redirect("admin_driver_trip_summary", driver_id=trip.driver.driverprofile.id)

    return render(request, "trips/edit_trip.html", {"trip": trip})

@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    driver_id = trip.driver.driverprofile.id

    trip.delete()
    messages.success(request, "Trip deleted successfully")

    return redirect("driver_trip_summary", driver_id=driver_id)

def get_date_range(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            return start_date, end_date
        except ValueError:
            return None, None

    return None, None