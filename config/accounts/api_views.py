from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import DriverProfile

@api_view(["POST"])
@permission_classes([AllowAny])
def driver_login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    if user.is_staff:
        return Response({"error": "Admin cannot login here"}, status=403)

    refresh = RefreshToken.for_user(user)
    profile = DriverProfile.objects.get(user=user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "driver": {
            "id": profile.id,
            "username": user.username,
            "vehicle": profile.vehicle.vehicle_number if profile.vehicle else None,
        }
    })
