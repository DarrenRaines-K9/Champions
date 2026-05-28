from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Wipe all seeded data and return the database to a clean migrated state. Dev only."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("flush_data is only allowed when DEBUG=True. Aborting.")

        confirm = input("This will delete ALL data. Type 'yes' to confirm: ")
        if confirm.strip().lower() != "yes":
            self.stdout.write("Aborted.")
            return

        from django.contrib.auth.models import User

        from events.models import Event, EventFoodNeed, FoodItem, Location, Signup
        from volunteers.models import Skill, Volunteer

        counts = {}

        # Delete in reverse FK order to avoid constraint errors.
        counts["Signup"] = Signup.all_objects.all().delete()[0]
        counts["EventFoodNeed"] = EventFoodNeed.objects.all().delete()[0]
        counts["Event"] = Event.all_objects.all().delete()[0]
        counts["Location"] = Location.objects.all().delete()[0]
        counts["FoodItem"] = FoodItem.objects.all().delete()[0]
        counts["Volunteer"] = Volunteer.all_objects.all().delete()[0]
        counts["Skill"] = Skill.objects.all().delete()[0]
        counts["User (non-superuser)"] = User.objects.filter(is_superuser=False).delete()[0]

        for model, n in counts.items():
            self.stdout.write(f"  Deleted {n} {model} record(s)")

        self.stdout.write(self.style.SUCCESS("Database flushed."))
