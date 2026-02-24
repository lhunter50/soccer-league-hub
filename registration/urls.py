from django.urls import path
from .views import CreateTeamRegistrationView, JoinTeamRegistrationView, InviteInfoView

urlpatterns = [
    path("registrations/team", CreateTeamRegistrationView.as_view()),
    path("registration/join", JoinTeamRegistrationView.as_view()),
    path("invites/<str:token>", InviteInfoView.as_view())
]
