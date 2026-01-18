from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('pokemon/<int:pokemon_id>/', views.pokemon_detail, name='pokemon_detail'),
    path('teams/', views.team, name='team'),
    path('fights/', views.fight, name='fight'),
]

