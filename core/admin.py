from django.contrib import admin
from .models import Organization, Membership

# Register your models here.

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
  list_display = ("name", "slug", "timezone", "is_active", "created_at")
  search_fields = ("name", "slugs")
  list_filter = ("is_active",)

class MembershipAdmin(admin.ModelAdmin):
  list_display = ("organization", "user", "role", "created_at")
  search_fields = ("organization__name", "organization__slug", "user__email", "user__username")
  list_filter = ("role", "organization")