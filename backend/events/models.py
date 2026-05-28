from decimal import Decimal

from django.db import models
from django.utils import timezone
from safedelete.models import SOFT_DELETE_CASCADE, SafeDeleteModel
from simple_history.models import HistoricalRecords


class Location(models.Model):
    name = models.CharField(max_length=200)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    # Plain DecimalFields for MVP — PostGIS PointField lands in Milestone 10.
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    notes = models.TextField(
        blank=True, help_text="Parking, accessibility, site-specific instructions."
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} — {self.city}, {self.state}"


class FoodItem(models.Model):
    class Category(models.TextChoices):
        ENTREE = "entree", "Entrée"
        SIDE = "side", "Side"
        DRINK = "drink", "Drink"
        DESSERT = "dessert", "Dessert"
        SUPPLY = "supply", "Supply"

    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Event(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="events")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    capacity = models.PositiveIntegerField(default=0, help_text="0 means unlimited.")
    meals_planned = models.PositiveIntegerField(default=0)
    food_items = models.ManyToManyField(FoodItem, through="EventFoodNeed", blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.title} — {self.date}"

    @property
    def volunteer_count(self) -> int:
        return self.signups.exclude(status="cancelled").count()

    @property
    def is_full(self) -> bool:
        if self.capacity == 0:
            return False
        return self.volunteer_count >= self.capacity


class EventFoodNeed(models.Model):
    class Unit(models.TextChoices):
        COUNT = "count", "Count"
        LBS = "lbs", "Lbs"
        GALLONS = "gallons", "Gallons"
        CASES = "cases", "Cases"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="food_needs")
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name="event_needs")
    quantity_needed = models.DecimalField(max_digits=8, decimal_places=2)
    quantity_committed = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    unit = models.CharField(max_length=20, choices=Unit.choices, default=Unit.COUNT)

    class Meta:
        unique_together = [("event", "food_item")]
        ordering = ["food_item__category", "food_item__name"]

    def __str__(self):
        return f"{self.event} — {self.food_item.name}"

    @property
    def shortage(self) -> Decimal:
        return max(self.quantity_needed - self.quantity_committed, Decimal("0"))

    @property
    def is_fulfilled(self) -> bool:
        return self.quantity_committed >= self.quantity_needed


class Signup(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    class Role(models.TextChoices):
        FOOD_PREP = "food_prep", "Food Prep"
        SERVING = "serving", "Serving"
        SETUP = "setup", "Setup"
        CLEANUP = "cleanup", "Cleanup"
        DRIVER = "driver", "Driver"
        LOGISTICS = "logistics", "Logistics"

    class Status(models.TextChoices):
        SIGNED_UP = "signed_up", "Signed Up"
        CONFIRMED = "confirmed", "Confirmed"
        ATTENDED = "attended", "Attended"
        NO_SHOW = "no_show", "No Show"
        CANCELLED = "cancelled", "Cancelled"

    volunteer = models.ForeignKey(
        "volunteers.Volunteer", on_delete=models.CASCADE, related_name="signups"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="signups")
    role = models.CharField(max_length=20, choices=Role.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SIGNED_UP)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    # Capped at 500 chars; rendered with Django's built-in HTML escaping.
    additional_donations = models.CharField(max_length=500, blank=True)

    history = HistoricalRecords()

    class Meta:
        unique_together = [("volunteer", "event")]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.volunteer} @ {self.event} ({self.get_status_display()})"

    @property
    def hours_worked(self) -> float:
        """
        Fallback hierarchy (spec section 4):
        1. Both check_in + check_out → use actual times.
        2. check_in only + event completed → use event.end_time as implicit checkout.
        3. Neither + status attended → use scheduled shift duration.
        4. no_show or cancelled → 0.
        """
        if self.status in (self.Status.NO_SHOW, self.Status.CANCELLED):
            return 0.0

        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            return round(delta.total_seconds() / 3600, 2)

        if self.check_in_time and self.event.status == Event.Status.COMPLETED:
            checkout = timezone.datetime.combine(
                self.event.date,
                self.event.end_time,
                tzinfo=timezone.get_current_timezone(),
            )
            delta = checkout - self.check_in_time
            return round(max(delta.total_seconds(), 0) / 3600, 2)

        if self.status == self.Status.ATTENDED:
            start = self.shift_start or self.event.start_time
            end = self.shift_end or self.event.end_time
            if start and end:
                today = timezone.now().date()
                dt_start = timezone.datetime.combine(today, start)
                dt_end = timezone.datetime.combine(today, end)
                delta = dt_end - dt_start
                return round(max(delta.total_seconds(), 0) / 3600, 2)

        return 0.0
