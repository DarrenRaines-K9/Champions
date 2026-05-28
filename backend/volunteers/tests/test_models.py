import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from volunteers.models import Volunteer


@pytest.fixture
def make_volunteer(db):
    """Factory that creates a User + Volunteer with sensible defaults."""

    def _make(first="Jane", last="Doe", display_publicly=False, **kwargs):
        user = User.objects.create_user(
            username=f"{first.lower()}.{last.lower()}",
            first_name=first,
            last_name=last,
            password="test",
        )
        return Volunteer.objects.create(user=user, display_publicly=display_publicly, **kwargs)

    return _make


# ---------------------------------------------------------------------------
# display_name
# ---------------------------------------------------------------------------


class TestDisplayName:
    def test_private_returns_first_name_and_last_initial(self, make_volunteer):
        vol = make_volunteer(first="Marcus", last="Thompson", display_publicly=False)
        assert vol.display_name == "Marcus T."

    def test_public_returns_full_name(self, make_volunteer):
        vol = make_volunteer(first="Marcus", last="Thompson", display_publicly=True)
        assert vol.display_name == "Marcus Thompson"

    def test_no_last_name_returns_first_name_only(self, make_volunteer):
        vol = make_volunteer(first="DJ", last="", display_publicly=False)
        assert vol.display_name == "DJ"

    def test_no_names_falls_back_to_username(self, db):
        user = User.objects.create_user(username="dj_cool", first_name="", last_name="")
        vol = Volunteer.objects.create(user=user, display_publicly=False)
        assert vol.display_name == "dj_cool"


# ---------------------------------------------------------------------------
# active_signup_count
# ---------------------------------------------------------------------------


class TestActiveSignupCount:
    def test_counts_future_non_cancelled_signups(self, make_volunteer, db):
        from events.models import Event, Location, Signup

        vol = make_volunteer()
        loc = Location.objects.create(
            name="Test Loc", street="1 Main", city="Nashville", state="TN", zip_code="37201"
        )
        future = (timezone.now() + timezone.timedelta(days=7)).date()

        event = Event.objects.create(
            title="Future Event",
            date=future,
            start_time="11:00",
            end_time="14:00",
            location=loc,
        )
        Signup.objects.create(volunteer=vol, event=event, role="serving", status="signed_up")
        assert vol.active_signup_count == 1

    def test_cancelled_signups_not_counted(self, make_volunteer, db):
        from events.models import Event, Location, Signup

        vol = make_volunteer()
        loc = Location.objects.create(
            name="Test Loc 2", street="2 Main", city="Nashville", state="TN", zip_code="37201"
        )
        future = (timezone.now() + timezone.timedelta(days=7)).date()

        event = Event.objects.create(
            title="Cancelled Signup Event",
            date=future,
            start_time="11:00",
            end_time="14:00",
            location=loc,
        )
        Signup.objects.create(volunteer=vol, event=event, role="serving", status="cancelled")
        assert vol.active_signup_count == 0

    def test_past_events_not_counted(self, make_volunteer, db):
        from events.models import Event, Location, Signup

        vol = make_volunteer()
        loc = Location.objects.create(
            name="Test Loc 3", street="3 Main", city="Nashville", state="TN", zip_code="37201"
        )
        past = (timezone.now() - timezone.timedelta(days=7)).date()

        event = Event.objects.create(
            title="Past Event",
            date=past,
            start_time="11:00",
            end_time="14:00",
            location=loc,
            status="completed",
        )
        Signup.objects.create(volunteer=vol, event=event, role="serving", status="attended")
        assert vol.active_signup_count == 0


# ---------------------------------------------------------------------------
# recent_no_show_count
# ---------------------------------------------------------------------------


class TestRecentNoShowCount:
    def test_counts_no_shows_within_90_days(self, make_volunteer, db):
        from events.models import Event, Location, Signup

        vol = make_volunteer()
        loc = Location.objects.create(
            name="NS Loc", street="4 Main", city="Nashville", state="TN", zip_code="37201"
        )
        recent = (timezone.now() - timezone.timedelta(days=30)).date()
        event = Event.objects.create(
            title="NS Event",
            date=recent,
            start_time="11:00",
            end_time="14:00",
            location=loc,
            status="completed",
        )
        signup = Signup.objects.create(volunteer=vol, event=event, role="serving", status="no_show")
        # Back-date created_at into the 90-day window
        Signup.objects.filter(pk=signup.pk).update(
            created_at=timezone.now() - timezone.timedelta(days=30)
        )
        assert vol.recent_no_show_count == 1

    def test_old_no_shows_not_counted(self, make_volunteer, db):
        from events.models import Event, Location, Signup

        vol = make_volunteer()
        loc = Location.objects.create(
            name="Old NS Loc", street="5 Main", city="Nashville", state="TN", zip_code="37201"
        )
        old = (timezone.now() - timezone.timedelta(days=120)).date()
        event = Event.objects.create(
            title="Old NS Event",
            date=old,
            start_time="11:00",
            end_time="14:00",
            location=loc,
            status="completed",
        )
        signup = Signup.objects.create(volunteer=vol, event=event, role="serving", status="no_show")
        Signup.objects.filter(pk=signup.pk).update(
            created_at=timezone.now() - timezone.timedelta(days=120)
        )
        assert vol.recent_no_show_count == 0
