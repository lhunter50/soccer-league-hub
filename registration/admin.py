from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from leagues.models import TeamInviteToken  # adjust if different app label
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


@admin.register(RegistrationRequest)
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
  list_filter = ("request_type", "status", "season")
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

  # add a button in the top right of changelist (optional nice-to-have)
  change_list_template = "admin/registration/registrationrequest/change_list.html"

  def get_urls(self):
      urls = super().get_urls()
      custom = [
          path(
              "test-join/",
              self.admin_site.admin_view(self.test_join_view),
              name="registration_registrationrequest_test_join",
          ),
      ]
      return custom + urls

  def test_join_view(self, request):
      """
      Admin-only test tool: create a JOIN_TEAM RegistrationRequest from an invite token.
      """
      if request.method == "POST":
          token = (request.POST.get("token") or "").strip()
          full_name = (request.POST.get("full_name") or "").strip()
          email = (request.POST.get("email") or "").strip()
          phone = (request.POST.get("phone") or "").strip() 
          waiver_file = request.FILES.get("waiver_file")
          id_file = request.FILES.get("id_file")
          

          if not token or not full_name:
              messages.error(request, "Token and full name are required.")
              return redirect("admin:registration_registrationrequest_test_join")

          try:
              invite = TeamInviteToken.objects.select_related(
                  "team_season",
                  "team_season__season",
                  "team_season__team",
              ).get(token=token, is_active=True)
          except TeamInviteToken.DoesNotExist:
              messages.error(request, "Invalid or inactive token.")
              return redirect("admin:registration_registrationrequest_test_join")

          ts = invite.team_season

          rr = RegistrationRequest.objects.create(
              request_type=RegistrationRequest.RequestType.JOIN_TEAM,
              status=RegistrationRequest.Status.PENDING,
              season=ts.season,
              team_season=ts,
              full_name=full_name,
              email=email,
              phone=phone,
              waiver_file=waiver_file,
              id_file=id_file
          )

          messages.success(
              request,
              f"Created JOIN_TEAM request for {ts.team.name} ({getattr(ts.season, 'name', ts.season)}). "
              f"Request ID: {rr.id}",
          )
          return redirect("admin:registration_registrationrequest_changelist")

      context = dict(
          self.admin_site.each_context(request),
          title="Test player join (create JOIN_TEAM request)",
      )
      return render(request, "admin/registration/registrationrequest/test_join.html", context)

  def get_changeform_initial_data(self, request):
      return {
          "request_type": RegistrationRequest.RequestType.CREATE_TEAM,
          "status": RegistrationRequest.Status.PENDING,
      }

  def approve_link(self, obj: RegistrationRequest):
      if obj.status != RegistrationRequest.Status.PENDING:
          return "-"
      return "Use action ↑"
  approve_link.short_description = "Approve"

  def save_model(self, request, obj, form, change):
      if obj.request_type == RegistrationRequest.RequestType.CREATE_TEAM and not obj.team_name_text.strip():
          messages.warning(request, "CREATE_TEAM request should have team_name_text.")
      if obj.request_type == RegistrationRequest.RequestType.JOIN_TEAM and not obj.team_season_id:
          messages.warning(request, "JOIN_TEAM request should have team_season.")
      super().save_model(request, obj, form, change)