import uuid
from django.conf import settings
from django.db import models

# Create your models here.
class Organization(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField(max_length=200)
  slug = models.SlugField(max_length=80, unique=True)
  timezone = models.CharField(max_length=80, default="America/Winnipeg")
  is_active = models.BooleanField(default=True)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self) -> str:
    return self.name
  
class Membership(models.Model):
  class Role(models.TextChoices):
    ORG_ADMIN = "ORG_ADMIN", "Org Admin"
    LEAGUE_ADMIN = "LEAGUE_ADMIN", "League Admin"
    TEAM_MANAGER = "TEAM_MANAGER", "Team Manager"
    READONLY = "READONLY", "Read Only"

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
  role = models.CharField(max_length=20, choices=Role.choices)

  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    constraints = {
      models.UniqueConstraint(fields=["organization", "name"], name="uniq_membership_org_user")
    }

  def __str__(self) -> str:
    return f"{self.user_id} -> {self.organization.slug} ({self.role})"