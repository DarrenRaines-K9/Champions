"""
Seed the database with realistic test data that exercises every UI state.
Idempotent — safe to run multiple times without duplicating data.

Spec (Milestone 1):
- 5 locations across varied cities
- 8 skills
- 12 volunteers (6 public, 6 private), each with 2-4 skills
- 12 events: 4 past, 8 upcoming (1 cancelled, 1 at full capacity)
- 15 food items across all categories
- 2-4 food needs per event, several deliberately unfulfilled
- ~40 signups across all statuses including edge cases for hours_worked fallback
- 1 volunteer with 2+ no-shows in past 90 days (triggers warning badge)
"""

import random
from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Event, EventFoodNeed, FoodItem, Location, Signup
from volunteers.models import Skill, Volunteer

TODAY = date.today()


class Command(BaseCommand):
    help = "Seed the database with realistic test data. Idempotent."

    def handle(self, *args, **options):
        self.stdout.write("Seeding locations...")
        locations = self._seed_locations()

        self.stdout.write("Seeding skills...")
        skills = self._seed_skills()

        self.stdout.write("Seeding food items...")
        food_items = self._seed_food_items()

        self.stdout.write("Seeding volunteers...")
        volunteers = self._seed_volunteers(skills)

        self.stdout.write("Seeding events...")
        events = self._seed_events(locations)

        self.stdout.write("Seeding food needs...")
        self._seed_food_needs(events, food_items)

        self.stdout.write("Seeding signups...")
        self._seed_signups(volunteers, events)

        self.stdout.write(self.style.SUCCESS("Seed complete."))

    # ------------------------------------------------------------------

    def _seed_locations(self):
        data = [
            {
                "name": "Downtown Community Center",
                "street": "201 Main St",
                "city": "Nashville",
                "state": "TN",
                "zip_code": "37201",
                "latitude": "36.165830",
                "longitude": "-86.784439",
            },
            {
                "name": "Eastside Food Hub",
                "street": "845 Gallatin Ave",
                "city": "Nashville",
                "state": "TN",
                "zip_code": "37206",
                "latitude": "36.180100",
                "longitude": "-86.741200",
            },
            {
                "name": "Grace Fellowship Church",
                "street": "1100 Church St",
                "city": "Murfreesboro",
                "state": "TN",
                "zip_code": "37130",
                "latitude": "35.849400",
                "longitude": "-86.390100",
            },
            {
                "name": "Hope Outreach Shelter",
                "street": "320 Lafayette St",
                "city": "Clarksville",
                "state": "TN",
                "zip_code": "37040",
                "latitude": "36.529800",
                "longitude": "-87.359400",
            },
            {
                "name": "Riverside Park Pavilion",
                "street": "50 Shelby Ave",
                "city": "Nashville",
                "state": "TN",
                "zip_code": "37206",
                "latitude": "36.163900",
                "longitude": "-86.763100",
                "notes": "Enter from Shelby Ave gate. Parking in Lot C.",
            },
        ]
        locations = []
        for d in data:
            obj, _ = Location.objects.get_or_create(name=d["name"], defaults=d)
            locations.append(obj)
        return locations

    def _seed_skills(self):
        names = [
            "Food handling certified",
            "Driver (has vehicle)",
            "Spanish speaker",
            "First aid certified",
            "Setup & logistics",
            "Serving experience",
            "Kitchen prep",
            "Photography",
        ]
        skills = []
        for name in names:
            obj, _ = Skill.objects.get_or_create(name=name)
            skills.append(obj)
        return skills

    def _seed_food_items(self):
        data = [
            ("Chili", FoodItem.Category.ENTREE),
            ("Lasagna", FoodItem.Category.ENTREE),
            ("Chicken & Rice", FoodItem.Category.ENTREE),
            ("Hot Dogs", FoodItem.Category.ENTREE),
            ("Green Beans", FoodItem.Category.SIDE),
            ("Corn", FoodItem.Category.SIDE),
            ("Coleslaw", FoodItem.Category.SIDE),
            ("Dinner Rolls", FoodItem.Category.SIDE),
            ("Lemonade", FoodItem.Category.DRINK),
            ("Water (cases)", FoodItem.Category.DRINK),
            ("Coffee", FoodItem.Category.DRINK),
            ("Brownies", FoodItem.Category.DESSERT),
            ("Cookies", FoodItem.Category.DESSERT),
            ("Serving Gloves", FoodItem.Category.SUPPLY),
            ("Foil Pans", FoodItem.Category.SUPPLY),
        ]
        items = []
        for name, category in data:
            obj, _ = FoodItem.objects.get_or_create(name=name, defaults={"category": category})
            items.append(obj)
        return items

    def _seed_volunteers(self, skills):
        profiles = [
            # (first, last, email, public, skill_indices)
            ("Marcus", "Thompson", "marcus@example.com", True, [0, 1, 5]),
            ("Priya", "Sharma", "priya@example.com", True, [2, 6, 7]),
            ("Jordan", "Williams", "jordan@example.com", True, [3, 4]),
            ("Elena", "Garcia", "elena@example.com", True, [0, 2, 5, 6]),
            ("Devon", "Okafor", "devon@example.com", True, [1, 4, 7]),
            ("Samira", "Hassan", "samira@example.com", True, [0, 3]),
            ("Tyler", "Brooks", "tyler@example.com", False, [1, 5]),
            ("Nguyen", "Tran", "nguyen@example.com", False, [2, 6]),
            ("Alexis", "Rivera", "alexis@example.com", False, [0, 4]),
            ("Chris", "Morgan", "chris@example.com", False, [3, 5, 7]),
            ("Jamie", "Lee", "jamie@example.com", False, [1, 2]),
            # Volunteer with 2+ no-shows — triggers warning badge
            ("Pat", "Nolan", "pat@example.com", False, [0]),
        ]
        volunteers = []
        for first, last, email, public, skill_idx in profiles:
            user, _ = User.objects.get_or_create(
                username=email,
                defaults={"first_name": first, "last_name": last, "email": email},
            )
            vol, _ = Volunteer.objects.get_or_create(
                user=user,
                defaults={"display_publicly": public},
            )
            vol.skills.set([skills[i] for i in skill_idx])
            volunteers.append(vol)
        return volunteers

    def _seed_events(self, locations):
        events_data = [
            # --- Past events (4) ---
            {
                "title": "Spring Feed — April",
                "date": TODAY - timedelta(days=60),
                "status": Event.Status.COMPLETED,
                "capacity": 12,
                "meals_planned": 80,
                "location": locations[0],
            },
            {
                "title": "Easter Community Meal",
                "date": TODAY - timedelta(days=45),
                "status": Event.Status.COMPLETED,
                "capacity": 15,
                "meals_planned": 120,
                "location": locations[1],
            },
            {
                "title": "May Day Feed",
                "date": TODAY - timedelta(days=28),
                "status": Event.Status.COMPLETED,
                "capacity": 10,
                "meals_planned": 75,
                "location": locations[2],
            },
            {
                "title": "Memorial Weekend Cookout",
                "date": TODAY - timedelta(days=7),
                "status": Event.Status.COMPLETED,
                "capacity": 20,
                "meals_planned": 150,
                "location": locations[4],
            },
            # --- Upcoming events (8) ---
            {
                "title": "June Community Lunch",
                "date": TODAY + timedelta(days=3),
                "status": Event.Status.ACTIVE,
                "capacity": 10,
                "meals_planned": 90,
                "location": locations[0],
            },
            {
                "title": "Weekend Dinner Drive",
                "date": TODAY + timedelta(days=7),
                "status": Event.Status.PLANNED,
                "capacity": 8,
                "meals_planned": 60,
                "location": locations[1],
            },
            # Full capacity — for "Full" badge testing
            {
                "title": "Eastside Block Meal",
                "date": TODAY + timedelta(days=10),
                "status": Event.Status.PLANNED,
                "capacity": 4,
                "meals_planned": 40,
                "location": locations[1],
            },
            {
                "title": "River Park Feed",
                "date": TODAY + timedelta(days=14),
                "status": Event.Status.PLANNED,
                "capacity": 15,
                "meals_planned": 100,
                "location": locations[4],
            },
            {
                "title": "Clarksville Outreach",
                "date": TODAY + timedelta(days=21),
                "status": Event.Status.PLANNED,
                "capacity": 12,
                "meals_planned": 85,
                "location": locations[3],
            },
            {
                "title": "Murfreesboro Mission Meal",
                "date": TODAY + timedelta(days=28),
                "status": Event.Status.PLANNED,
                "capacity": 10,
                "meals_planned": 70,
                "location": locations[2],
            },
            # Cancelled upcoming event
            {
                "title": "Postponed: North Side Feed",
                "date": TODAY + timedelta(days=35),
                "status": Event.Status.CANCELLED,
                "capacity": 8,
                "meals_planned": 50,
                "location": locations[0],
            },
            {
                "title": "Summer Kickoff Cookout",
                "date": TODAY + timedelta(days=42),
                "status": Event.Status.PLANNED,
                "capacity": 20,
                "meals_planned": 200,
                "location": locations[4],
            },
        ]

        events = []
        for d in events_data:
            obj, _ = Event.objects.get_or_create(
                title=d["title"],
                defaults={
                    "date": d["date"],
                    "start_time": time(11, 0),
                    "end_time": time(14, 0),
                    "status": d["status"],
                    "capacity": d["capacity"],
                    "meals_planned": d["meals_planned"],
                    "location": d["location"],
                },
            )
            events.append(obj)
        return events

    def _seed_food_needs(self, events, food_items):
        entrees = [f for f in food_items if f.category == FoodItem.Category.ENTREE]
        sides = [f for f in food_items if f.category == FoodItem.Category.SIDE]
        drinks = [f for f in food_items if f.category == FoodItem.Category.DRINK]
        supplies = [f for f in food_items if f.category == FoodItem.Category.SUPPLY]

        for event in events:
            needs = [
                (random.choice(entrees), "10.00", "8.00"),  # partially fulfilled
                (random.choice(sides), "5.00", "5.00"),  # fulfilled
                (random.choice(drinks), "4.00", "1.00"),  # shortage
                (random.choice(supplies), "6.00", "0.00"),  # not started
            ]
            seen = set()
            for food_item, needed, committed in needs:
                if food_item.pk in seen:
                    continue
                seen.add(food_item.pk)
                EventFoodNeed.objects.get_or_create(
                    event=event,
                    food_item=food_item,
                    defaults={
                        "quantity_needed": needed,
                        "quantity_committed": committed,
                        "unit": EventFoodNeed.Unit.COUNT,
                    },
                )

    def _seed_signups(self, volunteers, events):
        past_events = [e for e in events if e.date < TODAY]
        upcoming_events = [
            e for e in events if e.date >= TODAY and e.status != Event.Status.CANCELLED
        ]

        # --- Past event signups with realistic statuses ---
        for event in past_events:
            participants = random.sample(volunteers[:10], min(6, len(volunteers[:10])))
            for i, vol in enumerate(participants):
                status = Signup.Status.ATTENDED if i < 4 else Signup.Status.NO_SHOW
                check_in = None
                check_out = None
                if status == Signup.Status.ATTENDED:
                    check_in = timezone.make_aware(datetime.combine(event.date, time(11, 0)))
                    # One signup with check_in but no check_out (fallback case 2)
                    if i != 3:
                        check_out = timezone.make_aware(datetime.combine(event.date, time(14, 0)))
                Signup.objects.get_or_create(
                    volunteer=vol,
                    event=event,
                    defaults={
                        "role": random.choice([r[0] for r in Signup.Role.choices]),
                        "status": status,
                        "check_in_time": check_in,
                        "check_out_time": check_out,
                    },
                )

        # --- No-show volunteer (Pat Nolan, index 11) gets 2 recent no-shows ---
        pat = volunteers[11]
        for event in past_events[:2]:
            Signup.objects.get_or_create(
                volunteer=pat,
                event=event,
                defaults={
                    "role": Signup.Role.SERVING,
                    "status": Signup.Status.NO_SHOW,
                },
            )

        # --- Upcoming event signups ---
        for event in upcoming_events[:3]:
            participants = random.sample(volunteers[:8], min(4, len(volunteers[:8])))
            for vol in participants:
                Signup.objects.get_or_create(
                    volunteer=vol,
                    event=event,
                    defaults={
                        "role": random.choice([r[0] for r in Signup.Role.choices]),
                        "status": Signup.Status.SIGNED_UP,
                    },
                )

        # --- Fill the "Full" event (index 6, capacity=4) ---
        full_event = events[6]
        for vol in volunteers[:4]:
            Signup.objects.get_or_create(
                volunteer=vol,
                event=full_event,
                defaults={"role": Signup.Role.SERVING, "status": Signup.Status.CONFIRMED},
            )
