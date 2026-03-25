from django.db import models
from django.contrib.auth.models import User
from vehicles.models import Vehicle
from django.conf import settings
from django.db.models import Q

class Trip(models.Model):
    STATUS_CHOICES = (
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["driver"],
                condition=models.Q(status="OPEN"),
                name="only_one_open_trip_per_driver"
            )
        ]

    driver = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    company = models.CharField(
    max_length=255,
    null=True,
    blank=True
    )
    start_location = models.CharField(max_length=255)
    start_meter_reading = models.PositiveIntegerField(null=True, blank=True)
    end_meter_reading = models.PositiveIntegerField(null=True, blank=True)
    start_meter_image = models.ImageField(upload_to="meter/", null=True, blank=True)

    end_location = models.CharField(max_length=255, null=True, blank=True)
    end_meter_image = models.ImageField(upload_to="meter/", null=True, blank=True)

    ticket_no = models.CharField(max_length=100, null=True, blank=True)
    material = models.CharField(max_length=100, null=True, blank=True)
    net_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    drop_count = models.PositiveIntegerField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")
    @property
    def distance_km(self):
        if self.start_meter_reading is not None and self.end_meter_reading is not None:
            return self.end_meter_reading - self.start_meter_reading
        return None

class Salary(models.Model):
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_staff': False}
    )
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="salary_records"
    )
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver.username} - ₹{self.amount}"
