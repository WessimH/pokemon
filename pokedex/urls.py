from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("pokemon/<int:pokemon_id>/", views.pokemon_detail, name="pokemon_detail"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("capture/", views.capture_pokemon, name="capture_pokemon"),
    path("release/<int:pokemon_id>/", views.release_pokemon, name="release_pokemon"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("capture/<int:capture_id>/", views.capture_detail, name="capture_detail"),
    path("teams/", views.team, name="team"),
    path("fights/", views.fight, name="fight"),
]
