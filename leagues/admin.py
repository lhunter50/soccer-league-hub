from django.contrib import admin
from .models import (
    Season, Division, Team, TeamSeason, Venue,
    Match, MatchResult, TeamInviteToken, MatchAttendance
)

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "start_date", "end_date", "is_active", "created_at")
    list_filter = ("organization", "is_active")
    search_fields = ("name", "organization__name", "organization__slug")

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ("name", "season", "sort_order", "created_at")
    list_filter = ("season__organization", "season")
    search_fields = ("name", "season__name")

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "division", "primary_contact_name", "primary_contact_email", "is_active", "created_at")
    list_filter = ("division__season__organization", "division__season", "division", "is_active")
    search_fields = ("name", "primary_contact_name", "primary_contact_email")

@admin.register(TeamSeason)
class TeamSeasonAdmin(admin.ModelAdmin):
    list_display = ("team", "season", "status")
    list_filter = ("season__organization", "season", "status")
    search_fields = ("team__name", "season__name")

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "address", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("name", "address")

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("starts_at", "division", "home_team", "away_team", "venue", "status")
    list_filter = ("season__organization", "season", "division", "status", "venue")
    search_fields = ("home_team__name", "away_team__name", "division__name")
    date_hierarchy = "starts_at"

@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ("match", "home_score", "away_score", "is_forfeit", "recorded_at", "updated_at")
    list_filter = ("is_forfeit",)

@admin.register(TeamInviteToken)
class TeamInviteTokenAdmin(admin.ModelAdmin):
    list_display = ("team", "is_active", "created_at", "rotated_at")
    search_fields = ("team__name", "token")
    list_filter = ("is_active",)

@admin.register(MatchAttendance)
class MatchAttendanceAdmin(admin.ModelAdmin):
    list_display = ("match", "team", "participant_name", "status", "updated_at")
    list_filter = ("team", "status")
    search_fields = ("participant_name", "team__name")
