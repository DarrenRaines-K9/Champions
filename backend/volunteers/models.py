from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from safedelete.models import SOFT_DELETE_CASCADE, SafeDeleteModel
from simple_history.models import HistoricalRecords


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Volunteer(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="volunteer")
    phone = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name="volunteers")

    # Privacy — defaults False so new volunteers are private until they opt in.
    display_publicly = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self) -> str:
        """First name + last initial when private; full name when public."""
        first = self.user.first_name or self.user.username
        last = self.user.last_name
        if self.display_publicly and last:
            return f"{first} {last}"
        if last:
            return f"{first} {last[0]}."
        return first

    @property
    def active_signup_count(self) -> int:
        """Future signups not in cancelled status — used to enforce the cap."""
        return (
            self.signups.filter(
                event__date__gte=timezone.now().date(),
            )
            .exclude(status="cancelled")
            .count()
        )

    @property
    def recent_no_show_count(self) -> int:
        """No-show signups in the past 90 days — shown to coordinators as a warning."""
        cutoff = timezone.now() - timezone.timedelta(days=90)
        return self.signups.filter(
            status="no_show",
            created_at__gte=cutoff,
        ).count()
