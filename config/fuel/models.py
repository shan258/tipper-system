from django.db import models
from django.contrib.auth.models import User
from vehicles.models import Vehicle
from trips.models import Trip 

class FuelEntry(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    driver = models.ForeignKey(User, on_delete=models.CASCADE)
    diesel_liters = models.DecimalField(max_digits=6, decimal_places=2)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    meter_reading = models.IntegerField()
    bill_image = models.ImageField(upload_to="fuel_bills/", blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle} - {self.diesel_liters} L"

class ParkingEntry(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    end_meter_photo = models.ImageField(upload_to='parking/')
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle} - {self.driver} - {self.date}"
