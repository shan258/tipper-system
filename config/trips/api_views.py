from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from trips.models import Trip
from accounts.models import DriverProfile
from fuel.models import FuelEntry, ParkingEntry


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def open_trip_api(request):
    user = request.user

    start_location = request.data.get("start_location")
    start_meter_reading = request.data.get("start_meter_reading")

    if not start_location or not start_meter_reading:
        return Response(
            {"error": "start_location and start_meter_reading are required"},
            status=400
        )

    if Trip.objects.filter(driver=user, status="OPEN").exists():
        return Response(
            {"error": "Trip already open. Close it first."},
            status=400
        )

    profile = DriverProfile.objects.get(user=user)

    trip = Trip.objects.create(
        driver=user,
        vehicle=profile.vehicle,
        start_location=start_location,
        start_meter_reading=start_meter_reading,
        status="OPEN",
    )

    return Response({
        "success": True,
        "trip_id": trip.id,
        "vehicle": profile.vehicle.vehicle_number if profile.vehicle else None,
        "start_location": trip.start_location,
        "start_meter_reading": trip.start_meter_reading,
        "start_time": trip.start_time,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def close_trip_api(request):
    trip = Trip.objects.filter(
        driver=request.user,
        status="OPEN"
    ).first()

    if not trip:
        return Response({"error": "No open trip"}, status=400)

    trip.end_location = request.data.get("end_location")
    trip.end_meter_reading = request.data.get("end_meter_reading")
    trip.status = "CLOSED"
    trip.save()

    return Response({"success": True, "message": "Trip closed successfully"})
