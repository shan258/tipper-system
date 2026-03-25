from django.contrib import admin
from .models import FuelEntry
from .models import ParkingEntry

@admin.register(ParkingEntry)
class ParkingEntryAdmin(admin.ModelAdmin):
    list_display = ('driver', 'vehicle', 'date')


@admin.register(FuelEntry)
class FuelEntryAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle',
        'driver',
        'diesel_liters',
        'amount',
        'meter_reading',
        'date'
    )
