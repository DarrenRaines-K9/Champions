from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from .models import Skill, Volunteer


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Volunteer)
class VolunteerAdmin(SimpleHistoryAdmin):
    list_display = [
        "full_name",
        "email",
        "phone",
        "skill_count",
        "signup_count",
        "no_show_badge",
        "display_publicly",
    ]
    list_filter = ["display_publicly", "skills"]
    search_fields = ["user__first_name", "user__last_name", "user__email"]
    readonly_fields = ["display_name", "active_signup_count", "recent_no_show_count"]
    filter_horizontal = ["skills"]

    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

    full_name.short_description = "Name"

    def email(self, obj):
        return obj.user.email

    email.short_description = "Email"

    def skill_count(self, obj):
        return obj.skills.count()

    skill_count.short_description = "Skills"

    def signup_count(self, obj):
        return obj.signups.count()

    signup_count.short_description = "Signups"

    def no_show_badge(self, obj):
        count = obj.recent_no_show_count
        if count >= 2:
            return format_html(
                '<span style="color: #b91c1c; font-weight: bold;">⚠ {} no-shows</span>', count
            )
        return count

    no_show_badge.short_description = "No-shows (90d)"
