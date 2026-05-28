from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone

from events.models import Event, EventFoodNeed, FoodItem, Location, Signup
from volunteers.models import Volunteer

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def location(db):
    return Location.objects.create(
        name="Test Location", street="1 Main St", city="Nashville", state="TN", zip_code="37201"
    )


@pytest.fixture
def event(db, location):
    return Event.objects.create(
        title="Test Event",
        date=date.today() + timedelta(days=7),
        start_time=time(11, 0),
        end_time=time(14, 0),
        location=location,
        capacity=5,
        meals_planned=50,
    )


@pytest.fixture
def completed_event(db, location):
    return Event.objects.create(
        title="Completed Event",
        date=date.today() - timedelta(days=7),
        start_time=time(11, 0),
        end_time=time(14, 0),
        location=location,
        status=Event.Status.COMPLETED,
        capacity=10,
    )


@pytest.fixture
def volunteer(db):
    user = User.objects.create_user(username="vol1", first_name="Test", last_name="Vol")
    return Volunteer.objects.create(user=user)


@pytest.fixture
def food_item(db):
    return FoodItem.objects.create(name="Chili", category=FoodItem.Category.ENTREE)


# ---------------------------------------------------------------------------
# Event.volunteer_count
# ---------------------------------------------------------------------------


class TestVolunteerCount:
    def test_counts_active_signups(self, event, volunteer):
        Signup.objects.create(volunteer=volunteer, event=event, role="serving", status="signed_up")
        assert event.volunteer_count == 1

    def test_excludes_cancelled_signups(self, event, volunteer):
        Signup.objects.create(volunteer=volunteer, event=event, role="serving", status="cancelled")
        assert event.volunteer_count == 0

    def test_zero_when_no_signups(self, event):
        assert event.volunteer_count == 0


# ---------------------------------------------------------------------------
# Event.is_full
# ---------------------------------------------------------------------------


class TestIsFull:
    def test_full_when_at_capacity(self, event, volunteer):
        event.capacity = 1
        event.save()
        Signup.objects.create(volunteer=volunteer, event=event, role="serving", status="signed_up")
        assert event.is_full is True

    def test_not_full_below_capacity(self, event):
        assert event.is_full is False

    def test_unlimited_capacity_never_full(self, event, volunteer):
        event.capacity = 0
        event.save()
        Signup.objects.create(volunteer=volunteer, event=event, role="serving", status="signed_up")
        assert event.is_full is False


# ---------------------------------------------------------------------------
# EventFoodNeed.shortage / is_fulfilled
# ---------------------------------------------------------------------------


class TestFoodNeedProperties:
    def test_shortage_is_difference(self, event, food_item):
        need = EventFoodNeed.objects.create(
            event=event,
            food_item=food_item,
            quantity_needed=Decimal("10"),
            quantity_committed=Decimal("4"),
        )
        assert need.shortage == Decimal("6")

    def test_shortage_never_negative(self, event, food_item):
        need = EventFoodNeed.objects.create(
            event=event,
            food_item=food_item,
            quantity_needed=Decimal("4"),
            quantity_committed=Decimal("10"),
        )
        assert need.shortage == Decimal("0")

    def test_is_fulfilled_when_committed_meets_needed(self, event, food_item):
        need = EventFoodNeed.objects.create(
            event=event,
            food_item=food_item,
            quantity_needed=Decimal("5"),
            quantity_committed=Decimal("5"),
        )
        assert need.is_fulfilled is True

    def test_not_fulfilled_when_short(self, event, food_item):
        need = EventFoodNeed.objects.create(
            event=event,
            food_item=food_item,
            quantity_needed=Decimal("5"),
            quantity_committed=Decimal("3"),
        )
        assert need.is_fulfilled is False


# ---------------------------------------------------------------------------
# Signup.hours_worked — full fallback hierarchy
# ---------------------------------------------------------------------------


class TestHoursWorked:
    def _make_signup(self, volunteer, event, **kwargs):
        return Signup.objects.create(volunteer=volunteer, event=event, role="serving", **kwargs)

    def test_uses_actual_checkin_checkout(self, volunteer, event):
        check_in = timezone.make_aware(timezone.datetime(2026, 6, 1, 11, 0))
        check_out = timezone.make_aware(timezone.datetime(2026, 6, 1, 14, 0))
        signup = self._make_signup(
            volunteer, event, status="attended", check_in_time=check_in, check_out_time=check_out
        )
        assert signup.hours_worked == 3.0

    def test_uses_event_end_when_only_checkin_and_completed(self, volunteer, completed_event):
        check_in = timezone.make_aware(timezone.datetime.combine(completed_event.date, time(11, 0)))
        signup = self._make_signup(
            volunteer,
            completed_event,
            status="attended",
            check_in_time=check_in,
            check_out_time=None,
        )
        assert signup.hours_worked == 3.0

    def test_uses_shift_duration_when_attended_no_checkin(self, volunteer, event):
        signup = self._make_signup(
            volunteer,
            event,
            status="attended",
            shift_start=time(11, 0),
            shift_end=time(13, 30),
        )
        assert signup.hours_worked == 2.5

    def test_uses_event_times_when_no_shift_and_attended(self, volunteer, event):
        # event runs 11:00–14:00
        signup = self._make_signup(volunteer, event, status="attended")
        assert signup.hours_worked == 3.0

    def test_no_show_returns_zero(self, volunteer, event):
        signup = self._make_signup(volunteer, event, status="no_show")
        assert signup.hours_worked == 0.0

    def test_cancelled_returns_zero(self, volunteer, event):
        signup = self._make_signup(volunteer, event, status="cancelled")
        assert signup.hours_worked == 0.0

    def test_signed_up_with_no_checkin_returns_zero(self, volunteer, event):
        signup = self._make_signup(volunteer, event, status="signed_up")
        assert signup.hours_worked == 0.0


# ---------------------------------------------------------------------------
# Signup unique-together constraint
# ---------------------------------------------------------------------------


class TestSignupUniqueness:
    def test_duplicate_signup_raises(self, volunteer, event):
        Signup.objects.create(volunteer=volunteer, event=event, role="serving", status="signed_up")
        with pytest.raises(IntegrityError):
            Signup.objects.create(
                volunteer=volunteer, event=event, role="food_prep", status="signed_up"
            )
