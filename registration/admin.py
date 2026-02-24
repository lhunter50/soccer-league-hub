from django.contrib import admin, messages
from django.utils.html import format_html

from .models import RegistrationRequest
from .services import approve_create_team_request, approve_join_team_request


@admin.action(description="Approve selected registration requests")
def approve_selected(modeladmin, request, queryset):
  queryset = queryset.select_related("season", "team_season")
  approved = 0

  for req in queryset:
    if req.status != RegistrationRequest.Status.PENDING:
        continue

    try:
        if req.request_type == RegistrationRequest.RequestType.CREATE_TEAM:
            approve_create_team_request(req=req, approved_by=request.user)
            approved += 1
        elif req.request_type == RegistrationRequest.RequestType.JOIN_TEAM:
            approve_join_team_request(req=req, approved_by=request.user)
            approved += 1
    except Exception as e:
        messages.error(request, f"Failed approving {req.id}: {e}")

  messages.success(request, f"Approved {approved} request(s).")


class RegistrationRequestAdmin(admin.ModelAdmin):
  list_display = (
      "created_at",
      "request_type",
      "status",
      "season",
      "team_name_text",
      "team_season",
      "full_name",
      "email",
      "approve_link",
  )
  list_filter = ("request_type", "status", "season",)
  search_fields = ("full_name", "email", "team_name_text", "team_season__team__name")
  actions = [approve_selected]

  fieldsets = (
      ("Type & Status", {"fields": ("request_type", "status")}),
      ("Team Context", {"fields": ("season", "team_season", "team_name_text", "team_level", "team_notes")}),
      ("Person", {"fields": ("full_name", "email", "phone")}),
      ("Documents", {"fields": ("waiver_file", "id_file")}),
      ("Admin", {"fields": ("admin_notes", "approved_at", "approved_by", "rejected_at", "rejected_by")}),
  )
  readonly_fields = ("approved_at", "approved_by", "rejected_at", "rejected_by")

  def get_changeform_initial_data(self, request):
      """
      When you click 'Add Registration request', default it to CREATE_TEAM + PENDING
      so you can quickly create team registration requests for testing.
      """
      return {
          "request_type": RegistrationRequest.RequestType.CREATE_TEAM,
          "status": RegistrationRequest.Status.PENDING,
      }

  def approve_link(self, obj: RegistrationRequest):
      # Just a visual hint; real approval is via action or you can add a button later
      if obj.status != RegistrationRequest.Status.PENDING:
          return "-"
      return "Use action ↑"
  approve_link.short_description = "Approve"

  def save_model(self, request, obj, form, change):
    """
    Basic guardrails:
    - If CREATE_TEAM, team_name_text should be set.
    - If JOIN_TEAM, team_season should be set.
    """
    if obj.request_type == RegistrationRequest.RequestType.CREATE_TEAM and not obj.team_name_text.strip():
        messages.warning(request, "CREATE_TEAM request should have team_name_text.")
    if obj.request_type == RegistrationRequest.RequestType.JOIN_TEAM and not obj.team_season_id:
        messages.warning(request, "JOIN_TEAM request should have team_season.")
    super().save_model(request, obj, form, change)


admin.site.register(RegistrationRequest, RegistrationRequestAdmin)