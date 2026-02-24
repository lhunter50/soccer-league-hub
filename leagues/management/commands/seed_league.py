import random
import uuid
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from core.models import Organization
from leagues.models import Season, Division, Team, TeamSeason, Venue, Match, TeamMember

FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Casey", "Riley", "Morgan", "Jamie", "Avery", "Cameron", "Drew",
    "Sam", "Chris", "Pat", "Lee", "Jesse", "Kris", "Skyler", "Quinn", "Reese", "Parker"
]
LAST_NAMES = [
    "Smith", "Johnson", "Brown", "Miller", "Davis", "Wilson", "Moore", "Taylor", "Anderson", "Thomas",
    "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Lewis"
]

def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

class Command(BaseCommand):
    help = "Seed dummy league data (org/season/division/teams/rosters + optional scheduled matches)."

    def add_arguments(self, parser):
        parser.add_argument("--org-name", default="Coverall Soccer League")
        parser.add_argument("--org-slug", default="coverall")
        parser.add_argument("--season-name", default="Summer 2026")
        parser.add_argument("--division-name", default="Division 1")

        parser.add_argument("--teams", type=int, default=8)
        parser.add_argument("--players-per-team", type=int, default=10)

        parser.add_argument("--create-matches", action="store_true")
        parser.add_argument("--start-days-from-now", type=int, default=7)
        parser.add_argument("--games-per-week", type=int, default=2)
        parser.add_argument("--total-matches", type=int, default=20)

        parser.add_argument("--captains-have-users", action="store_true")
        parser.add_argument("--seed", type=int, default=42)

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(opts["seed"])

        org, _ = Organization.objects.get_or_create(
            slug=opts["org_slug"],
            defaults={"name": opts["org_name"]},
        )

        season, _ = Season.objects.get_or_create(
            organization=org,
            name=opts["season_name"],
            defaults={"is_active": True},
        )

        division, _ = Division.objects.get_or_create(
            season=season,
            name=opts["division_name"],
            defaults={"sort_order": 0},
        )

        venue, _ = Venue.objects.get_or_create(
            organization=org,
            name="Main Field",
            defaults={"address": "123 Soccer St", "is_active": True},
        )

        self.stdout.write(self.style.SUCCESS(
            f"Org={org.slug} | Season={season.name} | Division={division.name} | Venue={venue.name}"
        ))

        # Teams
        teams = list(Team.objects.filter(division=division).order_by("name"))
        to_create = max(0, opts["teams"] - len(teams))

        for i in range(to_create):
            idx = len(teams) + 1
            t = Team.objects.create(
                division=division,
                name=f"Team {idx}",
                short_name=f"T{idx}",
                primary_contact_name=rand_name(),
                primary_contact_email=f"captain{idx}@example.com",
                primary_contact_phone="204-555-0100",
                is_active=True,
            )
            teams.append(t)

        self.stdout.write(self.style.SUCCESS(f"Teams in division: {len(teams)}"))

        # TeamSeason
        team_seasons = []
        for t in teams:
            ts, _ = TeamSeason.objects.get_or_create(
                season=season,
                team=t,
                defaults={"status": TeamSeason.Status.ACTIVE},
            )
            team_seasons.append(ts)

        # TeamMembers (rosters)
        User = get_user_model()
        created_members = 0
        created_users = 0

        for ts in team_seasons:
            # Create captain
            captain_name = rand_name()
            captain_user = None

            if opts["captains_have_users"]:
                username = f"{ts.team.short_name.lower()}_capt_{uuid.uuid4().hex[:6]}"
                captain_user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password="password123!",
                )
                created_users += 1

            TeamMember.objects.create(
                team_season=ts,
                user=captain_user,
                role=TeamMember.Role.CAPTAIN,
                full_name=captain_name,
                jersey_number=1,
                is_active=True,
            )
            created_members += 1

            # Create players (no users)
            jersey = 2
            for _ in range(max(0, opts["players_per_team"] - 1)):
                TeamMember.objects.create(
                    team_season=ts,
                    user=None,
                    role=TeamMember.Role.PLAYER,
                    full_name=rand_name(),
                    jersey_number=jersey if jersey <= 99 else None,
                    is_active=True,
                )
                created_members += 1
                jersey += 1

        self.stdout.write(self.style.SUCCESS(
            f"Created TeamMembers: {created_members} | Created Users (captains): {created_users}"
        ))

        if not opts["create_matches"]:
            self.stdout.write(self.style.WARNING("Skipping matches (run with --create-matches to generate scheduled matches)."))
            return

        # Matches (scheduled only)
        pairings = []
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                pairings.append((teams[i], teams[j]))

        random.shuffle(pairings)
        pairings = pairings[: opts["total-matches"]]

        start_at = timezone.now() + timedelta(days=opts["start-days-from-now"])

        created_matches = 0
        for k, (home, away) in enumerate(pairings):
            dt = start_at + timedelta(days=(k // opts["games-per-week"]), hours=(k % opts["games-per-week"]) * 2)
            Match.objects.create(
                season=season,
                division=division,
                venue=venue,
                home_team=home,
                away_team=away,
                starts_at=dt,
                status=Match.Status.SCHEDULED,
                round_label=f"Round {k+1}",
                notes="Seeded match",
            )
            created_matches += 1

        self.stdout.write(self.style.SUCCESS(f"Created scheduled Matches: {created_matches}"))
        self.stdout.write(self.style.SUCCESS("Done."))