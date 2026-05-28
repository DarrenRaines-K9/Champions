from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the Coordinator group with appropriate permissions. Idempotent."

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name="Coordinator")

        perms = [
            # Events app — full CRUD
            ("add_event", "events", "event"),
            ("change_event", "events", "event"),
            ("delete_event", "events", "event"),
            ("view_event", "events", "event"),
            ("add_signup", "events", "signup"),
            ("change_signup", "events", "signup"),
            ("delete_signup", "events", "signup"),
            ("view_signup", "events", "signup"),
            ("add_location", "events", "location"),
            ("change_location", "events", "location"),
            ("delete_location", "events", "location"),
            ("view_location", "events", "location"),
            ("add_fooditem", "events", "fooditem"),
            ("change_fooditem", "events", "fooditem"),
            ("delete_fooditem", "events", "fooditem"),
            ("view_fooditem", "events", "fooditem"),
            ("add_eventfoodneed", "events", "eventfoodneed"),
            ("change_eventfoodneed", "events", "eventfoodneed"),
            ("delete_eventfoodneed", "events", "eventfoodneed"),
            ("view_eventfoodneed", "events", "eventfoodneed"),
            # Volunteers app — read-only
            ("view_volunteer", "volunteers", "volunteer"),
            ("view_skill", "volunteers", "skill"),
        ]

        assigned = []
        for codename, app_label, model in perms:
            try:
                perm = Permission.objects.get_by_natural_key(codename, app_label, model)
                group.permissions.add(perm)
                assigned.append(codename)
            except Permission.DoesNotExist:
                self.stderr.write(f"Permission not found: {app_label}.{codename}")

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"{action} Coordinator group with {len(assigned)} permissions.")
        )
