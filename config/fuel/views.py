from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import FuelEntry
from django.utils.timezone import localdate
from .models import ParkingEntry
from django.db.models import Sum
from trips.models import Trip
from vehicles.models import Vehicle
from accounts.models import DriverProfile
from django.contrib import messages
from datetime import datetime
from django.urls import reverse
from .utils import notify_admin

@login_required
@user_passes_test(lambda u: not u.is_staff)
def add_fuel(request):
    driver_profile = get_object_or_404(DriverProfile, user=request.user)
    vehicle = driver_profile.vehicle

    if not vehicle:
        messages.error(request, "No vehicle assigned. Contact admin.")
        return redirect("driver_dashboard")

    if request.method == "POST":
        # OPTIONAL: attach last trip if exists (OPEN or CLOSED)
        trip = Trip.objects.filter(vehicle=vehicle).order_by("-start_time").first()

        FuelEntry.objects.create(
            vehicle=vehicle,
            trip=trip,
            driver=request.user,
            diesel_liters=request.POST.get("diesel_liters"),
            amount=request.POST.get("amount"),
            meter_reading=request.POST.get("meter_reading"),
            bill_image=request.FILES.get("bill_image"),
        )
        notify_admin(
            message=f"⛽ Fuel entry added by {request.user.username}",
            link="/fuel/admin/"
        )


        messages.success(request, "Fuel entry added successfully")
        return redirect("driver_dashboard")

    return render(request, "fuel/add_fuel.html", {
        "vehicle": vehicle
    })



@login_required
def admin_fuel_dashboard(request):
    fuels = FuelEntry.objects.select_related(
        "vehicle", "driver", "trip"
    ).order_by("-date")
    
    start_date, end_date = get_date_range(request)
    if start_date and end_date:
        fuels = fuels.filter(date__range=[start_date, end_date])

    return render(request, "admin/fuel_dashboard.html", {
        "fuels": fuels,
        "start_date": start_date,
        "end_date": end_date,
    })

@login_required
def mileage_report(request):
    vehicles = Vehicle.objects.all()
    report = []

    for v in vehicles:
        total_km = Trip.objects.filter(
            vehicle=v,
            status='CLOSED'
        ).aggregate(total=Sum('distance'))['total'] or 0

        total_diesel = FuelEntry.objects.filter(
            vehicle=v
        ).aggregate(total=Sum('diesel_liters'))['total'] or 0

        mileage = round(total_km / total_diesel, 2) if total_diesel > 0 else 0

        if mileage >= 3:
            status = "GOOD"
        elif mileage >= 2:
            status = "WARNING"
        else:
            status = "WASTAGE"

        report.append({
            'vehicle': v.vehicle_number,
            'total_km': total_km,
            'total_diesel': total_diesel,
            'mileage': mileage,
            'status': status
        })

    return render(request, 'admin/mileage_report.html', {
        'report': report
    })

@login_required
def trip_mileage_report(request):
    trips = Trip.objects.filter(
        status='CLOSED'
    ).select_related('vehicle', 'driver')

    report = []

    for trip in trips:
        fuel_used = FuelEntry.objects.filter(
            trip=trip   # ✅ SIMPLE & SAFE
        ).aggregate(
            total=Sum('diesel_liters')
        )['total'] or 0

        mileage = round(trip.distance / fuel_used, 2) if fuel_used > 0 else 0

        if mileage >= 3:
            status = "GOOD"
        elif mileage >= 2:
            status = "WARNING"
        else:
            status = "WASTAGE"

        report.append({
            'vehicle': trip.vehicle.vehicle_number,
            'driver': trip.driver.username,
            'from': trip.start_location,
            'to': trip.end_location,
            'distance': trip.distance,
            'fuel': fuel_used,
            'mileage': mileage,
            'status': status
        })

    return render(request, 'admin/trip_mileage_report.html', {
        'report': report
    })

@login_required
@user_passes_test(lambda u: not u.is_staff)
def fuel_entry(request):
    if request.method == "POST":
        # save fuel entry
        pass

    return render(request, "driver/fuel_entry.html")

@login_required
@user_passes_test(lambda u: not u.is_staff)
def parking_entry(request):
    driver_profile = get_object_or_404(DriverProfile, user=request.user)
    vehicle = driver_profile.vehicle

    if not vehicle:
        messages.error(request, "No vehicle assigned. Contact admin.")
        return redirect("driver_dashboard")

    if request.method == "POST":
        photo = request.FILES.get("end_meter_photo")

        if not photo:
            messages.error(request, "Please upload end meter photo")
            return redirect("driver_dashboard")

        ParkingEntry.objects.create(
            driver=request.user,
            vehicle=vehicle,
            end_meter_photo=photo,
            date=localdate()
        )
        notify_admin(
            message=f"🅿️ Parking entry added by {request.user.username}",
            link="/parking/admin/"
        )


        messages.success(request, "Parking entry saved")
        return redirect("driver_dashboard")

    return render(request, "fuel/parking_entry.html", {
        "vehicle": vehicle
    })

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

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_fuel(request, pk):
    fuel = get_object_or_404(FuelEntry, pk=pk)

    if request.method == "POST":
        fuel.diesel_liters = request.POST.get("diesel_liters")
        fuel.amount = request.POST.get("amount")
        fuel.meter_reading = request.POST.get("meter_reading")

        if request.FILES.get("bill_image"):
            fuel.bill_image = request.FILES.get("bill_image")

        fuel.save()
        messages.success(request, "Fuel entry updated")
        return redirect("admin-fuel-dashboard")

    return render(request, "admin/edit_fuel.html", {"fuel": fuel})

@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_fuel(request, pk):
    fuel = get_object_or_404(FuelEntry, pk=pk)
    fuel.delete()
    messages.success(request, "Fuel entry deleted")
    return redirect("admin-fuel-dashboard")

@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_parking(request, pk):
    parking = get_object_or_404(ParkingEntry, pk=pk)
    parking.delete()
    messages.success(request, "Parking deleted")
    return redirect(reverse("admin_dashboard"))
