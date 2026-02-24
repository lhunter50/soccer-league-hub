from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models

from leagues.models import Season, Division, TeamSeason

class RegistrationRequest(models.Model):
  class RequestType(models.TextChoices):
    CREATE_TEAM = "CREATE_TEAM", "Create Team"
    JOIN_TEAM = "JOIN_TEAM", "Join Team"

  class Status(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    NEEDS_INFO = "NEEDS_INFO", "Needs Info"

  class Level(models.TextChoices):
    HIGH_LEVEL = "HIGH_LEVEL", "High Level"
    MEDIUM_LEVEL = "MEDIUM_LEVEL", "Medium Level"
    LOW_LEVEL = "LOW_LEVEL", "Low Level"

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

  request_type = models.CharField(max_length=20, choices=RequestType.choices)
  status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
  team_level = models.CharField(max_length=20, choices=Level.choices, blank=True, default="")
  team_notes = models.TextField(blank=True)

  # Context
  season = models.ForeignKey(Season, on_delete=models.PROTECT, related_name="registration_requests")
  division = models.ForeignKey(Division, on_delete=models.PROTECT, blank=True, null=True, related_name="registration_requests")

  #JOIN_TEAM requests link to an existing TeamSeason
  team_season = models.ForeignKey(
    TeamSeason,
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name="registration_requests"
  )

  #CREATE_TEAM requests include type team name
  team_name_text = models.CharField(max_length=50, blank=True)

  #person detailts (captain or player)
  full_name = models.CharField(max_length=120)
  email = models.EmailField(blank=True)
  phone = models.CharField(max_length=30, blank=True)

  #Docs
  waiver_file = models.FileField(upload_to="registration/waivers/", blank=True)
  id_file = models.FileField(upload_to="registration/ids/", blank=True)

  #Admin workflow
  admin_notes = models.TextField(blank=True)

  approved_at = models.DateTimeField(null=True)
  rejected_at = models.DateTimeField(null=True)

  approved_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="approved_registration_requests"
  )
  rejected_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    blank=True,
    null=True,
    related_name="rejected_registration_requests"
  )

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self) -> str:
    return f"{self.request_type} - {self.full_name} - {self.status}"