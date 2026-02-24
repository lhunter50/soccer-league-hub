import uuid
import secrets
from django.db import models
from django.utils import timezone
from core.models import Organization
from django.db.models import Q, F
from django.core.exceptions import ValidationError

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Season(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="seasons")
  name = models.CharField(max_length=120)
  start_date = models.DateField(null=True, blank=True)
  end_date = models.DateField(null=True, blank=True)
  is_active = models.BooleanField(default=False)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=["organization", "name"], name="uniq_season_org_name")
    ]

  def __str__(self) -> str:
    return f"{self.organization.slug} - {self.name}"
  

class Division(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="divisions")
  name = models.CharField(max_length=120)
  sort_order = models.IntegerField(default=0)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=["season", "name"], name="uniq_division_season_name")
    ]

  def __str__(self) -> str:
    return f"{self.season.name} - {self.name}"
  
class Team(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name="teams")

  name = models.CharField(max_length=120)
  short_name = models.CharField(max_length=40, blank=True, default="")

  primary_contact_name = models.CharField(max_length=120, blank=True, default="")
  primary_contact_email = models.EmailField(blank=True, default="")
  primary_contact_phone = models.CharField(max_length=40, blank=True, default="")

  is_active = models.BooleanField(default=True)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=["division", "name"], name="uniq_team_division_name")
    ]
    indexes = [
      models.Index(fields=["division", "name"]),
      models.Index(fields=["is_active"]),
    ]

  def __str__(self) -> str:
    return self.name
  

class TeamSeason(models.Model):
  """
  Anchor for future payments (team owes fees to the league each season),
  We can keep history if teams carry over
  """

  class Status(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    WITHDRAWN = "WITHDRAWN", "Withdrawn"

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="team_seasons")
  team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_seasons")
  status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=["season", "team"], name="uniq_teamseason_season_team")
    ]

  def __str__(self) -> str:
    return f"{self.team.name} @ {self.season.name}"
  

class Venue(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="venues")
  name = models.CharField(max_length=120)
  address = models.CharField(max_length=255, blank=True, default="")
  notes = models.CharField(max_length=255, blank=True, default="")
  lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
  lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
  is_active = models.BooleanField(default=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=["organization", "name"], name="uniq_venue_org_name")
    ]

  def __str__(self) -> str:
    return self.name
  
class Match(models.Model):
  class Status(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    FINAL = "FINAL", "Final"
    CANCELLED = "CANCELLED", "Cancelled"
    POSTPONED = "POSTPONED", "Postponed"

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="matches")
  division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name="matches")
  venue = models.ForeignKey(Venue, on_delete=models.PROTECT, null=True, blank=True, related_name="matches")

  home_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="home_matches")
  away_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="away_matches")

  starts_at = models.DateTimeField()
  status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)
  round_label = models.CharField(max_length=80, blank=True, default="")
  notes = models.TextField(blank=True, default="")

  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    indexes = [
      models.Index(fields=["season", "starts_at"]),
      models.Index(fields=["division", "starts_at"]),
      models.Index(fields=["venue", "starts_at"]),
      models.Index(fields=["home_team", "starts_at"]),
      models.Index(fields=["away_team", "starts_at"]),
    ]
    constraints = [
      models.CheckConstraint(
        condition=~Q(home_team=F("away_team")),
        name="chk_match_home_away_different"
      )
    ]

  def __str__(self) -> str:
    return f"{self.home_team} vs {self.away_team} @ {self.starts_at}"
  
  def clean(self):
    errors = {}

    # division must belong to season
    if self.division_id and self.season_id:
      if self.division.season_id != self.season_id:
        errors["division"] = "Division must belong to the same season as the match"
    

    for field_name in ["home_team", "away_team"]:
      team = getattr(self, field_name)

      if team and self.division_id:
        if team.division_id != self.division_id:
          errors[field_name] = f"{field_name.replace('_', ' ').title()} must belong to the match division"

    if errors:
      raise ValidationError(errors)
  
class MatchResult(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name="result")

  home_score = models.IntegerField()
  away_score = models.IntegerField()
  is_forfeit = models.BooleanField(default=False)

  recorded_by = models.CharField(max_length=120, blank=True, default="")
  recorded_at = models.DateTimeField(default=timezone.now)
  updated_at = models.DateTimeField(auto_now=True)


# Attendance Lite (per team)
class TeamInviteToken(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  # team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name="invite_token")
  team_season = models.OneToOneField(TeamSeason, on_delete=models.CASCADE, related_name="invite_token")
  token = models.CharField(max_length=128, unique=True, db_index=True)
  is_active = models.BooleanField(default=True)

  created_at = models.DateTimeField(auto_now_add=True)
  rotated_at = models.DateTimeField(null=True, blank=True)

  @staticmethod
  def generate_token() -> str:
      return secrets.token_urlsafe(32)

  def rotate(self, *, save=True) -> None:
      self.token = self.generate_token()
      self.is_active = True
      self.rotated_at = timezone.now()
      if save:
        self.save(update_fields=["token", "is_active", "rotated_at"])


class MatchAttendance(models.Model):
  class Status(models.TextChoices):
      GOING = "GOING", "Going"
      MAYBE = "MAYBE", "Maybe"
      OUT = "OUT", "Out"

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="attendances")
  team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="attendances")

  participant_name = models.CharField(max_length=80)
  status = models.CharField(max_length=10, choices=Status.choices)
  note = models.CharField(max_length=255, blank=True, default="")
  device_key = models.CharField(max_length=64, blank=True, default="")
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
      constraints = [
          models.UniqueConstraint(
              fields=["match", "team", "participant_name"],
              name="uniq_attendance_match_team_name",
          )
      ]

class TeamMember(models.Model):
  class Role(models.TextChoices):
    CAPTAIN = "CAPTAIN", "Captain"
    PLAYER = "PLAYER", "Player"

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  team_season = models.ForeignKey("TeamSeason", on_delete=models.CASCADE, related_name="members")
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="team_memberships", null=True, blank=True)

  role = models.CharField(max_length=10, choices=Role.choices, default=Role.PLAYER)
  jersey_number = models.PositiveSmallIntegerField(
    null=True,
    blank=True,
    validators=[MinValueValidator(0), MaxValueValidator(99)]
  )
  full_name = models.CharField(max_length=120, null=True, blank=True)
  email = models.EmailField(blank=True, default="")
  phone = models.CharField(max_length=40, blank=True, default="")

  is_active = models.BooleanField(default=True)
  joined_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    constraints = [
      models.UniqueConstraint(fields=["team_season", "full_name"], name="uniq_teamseason_member_name")
    ]
    indexes = [
      models.Index(fields=["team_season", "role"]),
    ]

  def __str__(self):
    return f"{self.full_name} -- {self.team_season.team.name}"
  

class GoalEvent(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  match = models.ForeignKey("Match", on_delete=models.CASCADE, related_name="goal_events")
  team = models.ForeignKey("Team", on_delete=models.PROTECT, related_name="goal_events")
  scorer = models.ForeignKey("TeamMember", on_delete=models.PROTECT, related_name="goals")

  minute = models.PositiveSmallIntegerField(null=True, blank=True)

  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    indexes = [
      models.Index(fields=["match"]),
      models.Index(fields=["scorer"])
    ]
  def clean(self):
    if not self.match_id or not self.player_id:
        return  # let admin handle required field errors

    player_team_id = self.player.team_season.team_id

    # Auto-set team from player
    self.team_id = player_team_id

    if player_team_id not in (self.match.home_team_id, self.match.away_team_id):
        raise ValidationError({
            "player": "Player must belong to a team playing in this match."
        })

class CardEvent(models.Model):
  class Card(models.TextChoices):
    YELLOW = "YELLOW", "Yellow"
    RED = "RED", "Red"
  
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  match = models.ForeignKey("Match", on_delete=models.CASCADE, related_name="card_events")
  team = models.ForeignKey("Team", on_delete=models.PROTECT, related_name="card_events")
  player = models.ForeignKey("TeamMember", on_delete=models.PROTECT, related_name="cards")

  card = models.CharField(max_length=10, choices=Card.choices)
  minute = models.PositiveSmallIntegerField(null=True, blank=True)
  note = models.CharField(max_length=255, blank=True, default="")

  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    indexes = [
      models.Index(fields=["match"]),
      models.Index(fields=["player"]),
      models.Index(fields=["card"]),
    ]

  def clean(self):
    if not self.match_id or not self.player_id:
        return  # let admin handle required field errors

    player_team_id = self.player.team_season.team_id

    # Auto-set team from player
    self.team_id = player_team_id

    if player_team_id not in (self.match.home_team_id, self.match.away_team_id):
        raise ValidationError({
            "player": "Player must belong to a team playing in this match."
        })

class Appearance(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  match = models.ForeignKey("Match", on_delete=models.CASCADE, related_name="appearances")
  team = models.ForeignKey("Team", on_delete=models.PROTECT, related_name="appearances")
  player = models.ForeignKey("TeamMember", on_delete=models.PROTECT, related_name="appearances_as_player")

  class Meta:
    constraints = [
        models.UniqueConstraint(fields=["match", "player"], name="uniq_appearance_match_player"),
    ]
    indexes = [
        models.Index(fields=["match", "team"]),
        models.Index(fields=["player"]),
    ]

  def clean(self):
    if not self.match_id or not self.player_id:
        return  # let admin handle required field errors

    player_team_id = self.player.team_season.team_id

    # Auto-set team from player
    self.team_id = player_team_id

    if player_team_id not in (self.match.home_team_id, self.match.away_team_id):
        raise ValidationError({
            "player": "Player must belong to a team playing in this match."
        })