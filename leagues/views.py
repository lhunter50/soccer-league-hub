from django.shortcuts import get_list_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Organization
from .models import Match, Season
from .serializers import MatchPublicSerializer