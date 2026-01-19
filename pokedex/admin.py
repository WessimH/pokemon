from django.contrib import admin
from .models import PokemonCapture

# Register your models here.

# On crée une configuration simple pour l'admin
@admin.register(PokemonCapture)
class PokemonCaptureAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'level', 'in_team', 'captured_at') # Ce qu'on voit dans la liste
    list_filter = ('user', 'in_team') # Filtres sur la droite
    search_fields = ('name', 'user__username') # Barre de recherche
