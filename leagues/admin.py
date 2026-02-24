from django.contrib import admin
from .models import (
    Appearance, CardEvent, GoalEvent, Season, Division, Team, TeamMember, TeamSeason, Venue,
    Match, MatchResult, TeamInviteToken, MatchAttendance
)

# ---------- Inlines for Match entry ----------

class MatchResultInline(admin.StackedInline):
    model = MatchResult
    extra = 0
    max_num = 1


class AppearanceInline(admin.TabularInline):
    model = Appearance
    extra = 0
    fields = ("player",)  # remove "team" (recommended)

    def get_formset(self, request, obj=None, **kwargs):
        self._match_obj = obj
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "player":
            match = getattr(self, "_match_obj", None)
            if match:
                kwargs["queryset"] = TeamMember.objects.filter(
                    team_season__team_id__in=[match.home_team_id, match.away_team_id],
                    is_active=True,
                ).select_related("team_season__team")
            else:
                kwargs["queryset"] = TeamMember.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class GoalEventInline(admin.TabularInline):
    model = GoalEvent
    extra = 0
    fields = ("scorer", "minute")

    def get_formset(self, request, obj=None, **kwargs):
        self._match_obj = obj
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "scorer":
            match = getattr(self, "_match_obj", None)
            if match:
                kwargs["queryset"] = TeamMember.objects.filter(
                    team_season__team_id__in=[match.home_team_id, match.away_team_id],
                    is_active=True,
                ).select_related("team_season__team")
            else:
                kwargs["queryset"] = TeamMember.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CardEventInline(admin.TabularInline):
    model = CardEvent
    extra = 0
    fields = ("player", "card", "minute", "note")

    def get_formset(self, request, obj=None, **kwargs):
        self._match_obj = obj
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "player":
            match = getattr(self, "_match_obj", None)
            if match:
                kwargs["queryset"] = TeamMember.objects.filter(
                    team_season__team_id__in=[match.home_team_id, match.away_team_id],
                    is_active=True,
                ).select_related("team_season__team")
            else:
                kwargs["queryset"] = TeamMember.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
    inlines = [MatchResultInline, AppearanceInline, GoalEventInline, CardEventInline]

@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ("match", "home_score", "away_score", "is_forfeit", "recorded_at", "updated_at")
    list_filter = ("is_forfeit",)

# @admin.register(TeamInviteToken)
# class TeamInviteTokenAdmin(admin.ModelAdmin):
#     list_display = ("team", "is_active", "created_at", "rotated_at")
#     search_fields = ("team__name", "token")
#     list_filter = ("is_active",)

@admin.register(MatchAttendance)
class MatchAttendanceAdmin(admin.ModelAdmin):
    list_display = ("match", "team", "participant_name", "status", "updated_at")
    list_filter = ("team", "status")
    search_fields = ("participant_name", "team__name")


# ---------- Register Match result models ----------

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "team_season", "role", "jersey_number", "is_active", "joined_at")
    list_filter = ("team_season__season", "team_season__team", "role", "is_active")
    search_fields = ("display_name", "team_season__team__name")
    autocomplete_fields = ("team_season", )


@admin.register(GoalEvent)
class GoalEventAdmin(admin.ModelAdmin):
    list_display = ("match", "team", "scorer", "minute", "created_at")
    list_filter = ("match__season", "team",)
    search_fields = ("scorer__display_name", "team__name", "match__home_team__name", "match__away_team__name")
    autocomplete_fields = ("match", "team", "scorer")


@admin.register(CardEvent)
class CardEventAdmin(admin.ModelAdmin):
    list_display = ("match", "team", "player", "card", "minute", "created_at")
    list_filter = ("match__season", "card", "team")
    search_fields = ("player__display_name", "team__name", "match__home_team__name", "match__away_team__name")
    autocomplete_fields = ("match", "team", "player")


@admin.register(Appearance)
class AppearanceAdmin(admin.ModelAdmin):
    list_display = ("match", "team", "player")
    list_filter = ("match__season", "team")
    search_fields = ("player__display_name", "team__name", "match__home_team__name", "match__away_team__name")
    autocomplete_fields = ("match", "team", "player")