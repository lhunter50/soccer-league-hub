from __future__ import annotations

from rest_framework import serializers
from .models import RegistrationRequest
from leagues.models import TeamInviteToken

class TeamRegistrationSerializer(serializers.Serializer):
  class Meta:
    model = RegistrationRequest
    fields = ["id", "season", "team_name_text", "team_level" "full_name", "email", "phone", "team_notes"]

  def validate_team_name_text(self, value: str) -> str:
    if not value or not value.strip():
      raise serializers.ValidationError("Team name is required")
    return value.strip()
  
  def create(self, validated_data):
    validated_data["request_type"] = RegistrationRequest.RequestType.CREATE_TEAM
    validated_data["status"] = RegistrationRequest.Status.PENDING
    return super().create(validated_data)
  
class PlayerJoinRegistrationSerializer(serializers.Serializer):
  token = serializers.CharField(write_only=True)

  class Meta:
    model = RegistrationRequest
    fields = ["id", "token", "full_name", "email", "phone", "waiver_file", "id_file"]

  def validate(self, attrs):
    token = attrs.get("token")
    try:
      invite = (
        TeamInviteToken.objects.select_related("team_season", "team_season__team", "team_season__season").get(token=token)
      )
    except TeamInviteToken.DoesNotExist:
      raise serializers.ValidationError({"token": "Invalid invite link."})
    
    if not invite.is_active:
      raise serializers.ValidationError({"token": "Invite link is inactive"})
    
    attrs["_invite"] = invite
    return attrs
  
  def create(self, validated_data):
    invite = validated_data.pop("_invite")
    validated_data.pop = ("token", None)

    ts = invite.team_season
    return RegistrationRequest.objects.create(
      request_type=RegistrationRequest.RequestType.JOIN_TEAM,
      status=RegistrationRequest.Status.PENDING,
      season=ts.season,
      division=getattr(ts, "division", None),
      team_season=ts,
      **validated_data,
    )