from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import RegistrationRequest
from .serializers import TeamRegistrationSerializer, PlayerJoinRegistrationSerializer

from leagues.models import TeamInviteToken

class CreateTeamRegistrationView(generics.CreateAPIView):
  permission_classes = [permissions.AllowAny]
  serializer_class = TeamRegistrationSerializer
  queryset = RegistrationRequest.objects.all()

class JoinTeamRegistrationView(generics.CreateAPIView):
  permission_classes = [permissions.AllowAny]
  serializer_class = PlayerJoinRegistrationSerializer
  queryset = RegistrationRequest.objects.select_related("season", "team_season")

class InviteInfoView(APIView):
  permission_classes = [permissions.AllowAny]

  def get(self, request, token: str):
    invite = (
      TeamInviteToken.objects.select_related("team_season", "team_season__team", "team_season__season").get(token=token, is_active=True)
    )
    ts = invite.team_season
    return Response({
      "team": ts.team.name,
      "season": getattr(ts.season, "name", str(ts.season)),
      "division": getattr(getattr(ts, "division", None), "name", None)
    })