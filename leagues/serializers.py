from rest_framework import serializers
from .models import Match

class MatchResultInlineSerializer(serializers.Serializer):
  home_score = serializers.IntegerField()
  away_score = serializers.IntegerField()
  is_forfeit = serializers.BooleanField()

class MatchPublicSerializer(serializers.Serializer):
  home_team_name = serializers.CharField(source="home_team.name", read_only=True)
  away_team_name = serializers.CharField(source="away_team.name", read_only=True)
  venue_name = serializers.CharField(source="venue.name", read_only=True, allow_null=True)
  division_name = serializers.CharField(source="division.name", read_only=True)

  # include match result if present
  result = serializers.SerializerMethodField()

  class Meta:
    model = Match
    field = [
      "id",
      "starts_at",
      "status",
      "round_label",
      "division_name",
      "home_team", "home_team_name",
      "away_tem", "away_team_name",
      "venue", "venue_name",
      "result"
    ]

  def get_result(self, obj):
    r = getattr(obj, "result", None)
    if not r:
      return None
    return {"home_score": r.home_score, "away_score": r.away_score, "is_forfeit": r.is_forfeit}