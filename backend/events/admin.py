from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Event, EventFoodNeed, FoodItem, Location, Signup


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "state", "event_count"]
    search_fields = ["name", "city", "state"]

    def event_count(self, obj):
        return obj.events.count()

    event_count.short_description = "Events"


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category"]
    list_filter = ["category"]
    search_fields = ["name"]


class EventFoodNeedInline(admin.TabularInline):
    model = EventFoodNeed
    extra = 1
    fields = ["food_item", "quantity_needed", "quantity_committed", "unit"]
    readonly_fields = []


class SignupInline(admin.TabularInline):
    model = Signup
    extra = 0
    fields = ["volunteer", "role", "status", "check_in_time", "check_out_time"]
    readonly_fields = []
    show_change_link = True


@admin.register(Event)
class EventAdmin(SimpleHistoryAdmin):
    list_display = [
        "title",
        "date",
        "location",
        "status",
        "volunteer_count",
        "capacity",
        "meals_planned",
    ]
    list_filter = ["status", "location", "date"]
    search_fields = ["title", "location__name"]
    date_hierarchy = "date"
    inlines = [EventFoodNeedInline, SignupInline]
    readonly_fields = ["volunteer_count", "is_full"]

    def volunteer_count(self, obj):
        return obj.volunteer_count

    volunteer_count.short_description = "Volunteers"


@admin.register(Signup)
class SignupAdmin(SimpleHistoryAdmin):
    list_display = [
        "volunteer",
        "event",
        "role",
        "status",
        "check_in_time",
        "hours_worked",
        "created_at",
    ]
    list_filter = ["status", "role"]
    search_fields = ["volunteer__user__first_name", "volunteer__user__last_name", "event__title"]
    readonly_fields = ["hours_worked", "created_at"]
    actions = ["mark_attended", "mark_no_show"]

    def hours_worked(self, obj):
        return obj.hours_worked

    hours_worked.short_description = "Hours"

    @admin.action(description="Mark selected signups as attended")
    def mark_attended(self, request, queryset):
        queryset.update(status=Signup.Status.ATTENDED)

    @admin.action(description="Mark selected signups as no-show")
    def mark_no_show(self, request, queryset):
        queryset.update(status=Signup.Status.NO_SHOW)
