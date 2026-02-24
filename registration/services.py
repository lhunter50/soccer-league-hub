from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import RegistrationRequest
from leagues.models import Team, TeamSeason, TeamMember, TeamInviteToken

def _join_link(token: str) -> str:
  base = getattr(settings, "PUBLIC_APP_BASE_URL", "http://localhost:8000").rstrip("/")
  return f"{base}/register/join/{token}"

def _send_captain_link(*, to_email: str, team_name: str, season_label: str, token: str) -> None:
  link = _join_link(token)
  subject = f"Team approved: {team_name} ({season_label})"
  body = (
    f"Your team has been approved.\n\n"
    f"Share this link with your players to register:\n{link}\n\n"
    f"If you have any issues, please reply to this email."
  )
  send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)

@transaction.atomic
def approve_create_team_request(*, req: RegistrationRequest, approved_by=None) -> TeamSeason:
  if req.request_type != RegistrationRequest.RequestType.CREATE_TEAM:
    raise ValueError("Note a CREATE_TEAM request.")
  if req.status != RegistrationRequest.Status.PENDING:
    raise ValueError("Request is not PENDING.")
  
  team = Team.objects.create(name=req.team_name_text.strip())
  team_season = TeamSeason.objects.create(team=team, season=req.season,)

  #Captain record
  TeamMember.objects.create(
    team_season=team_season,
    full_name=req.full_name,
    user=None,
    role=TeamMember.Role.CAPTAIN
  )

  invite = TeamInviteToken.objects.create(team_season=team_season)
  #Ensure token exists
  if not invite.token:
    invite.rotate(save=True)

  req.team_season = team_season
  req.status = RegistrationRequest.Status.APPROVED
  req.approved_at = timezone.now()
  req.approved_by = approved_by
  req.save(update_fields=["team_season", "status", "approved_at", "approved_by", "updated_at"])

  if req.email:
    season_label = getattr(req.season, "name", str(req.season))
    _send_captain_link(
      to_email=req.email,
      team_name=team.name,
      season_label=season_label,
      token=invite.token,
    )
  return team_season

@transaction.atomic
def approve_join_team_request(*, req: RegistrationRequest, approved_by=None) -> TeamMember:
  if req.request_type != RegistrationRequest.RequestType.JOIN_TEAM:
    raise ValueError("Not a JOIN_TEAM request")
  if req.status != RegistrationRequest.Status.PENDING:
    raise ValueError(f"Request is not PENDING (current={req.status})")
  if not req.team_season_id:
    raise ValueError("JOIN_TEAM request missing team_season")
  
  member = TeamMember.objects.create(
    team_season=req.team_season,
    full_name=req.full_name,
    user=None,
    role=TeamMember.Role.PLAYER 
  ) 

  req.status = RegistrationRequest.Status.APPROVED
  req.approved_at = timezone.now()
  req.approved_by = approved_by
  req.save(update_fields=["status", "approved_at", "approved_by", "updated_at"])

  return member