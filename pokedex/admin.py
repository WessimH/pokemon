from django.contrib import admin
from django.core.exceptions import ValidationError
from django import forms

from .models import PokemonCapture, Team

# Register your models here.

# On crée une configuration simple pour l'admin
@admin.register(PokemonCapture)
class PokemonCaptureAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "level", "experience", "captured_at")
    list_filter = ("user", "level")
    search_fields = ("name", "user__username")


# Formulaire personnalisé pour empêcher les admins de mettre plus de 5 Pokémons dans une équipe
# Cette validation est obligée car le modèle Team.clean() n'est pas appelé
class TeamAdminForm(forms.ModelForm): 
    # on se base sur le form de classique 
    class Meta:
        model = Team
        fields = '__all__'
    
    # on ajoute le check sur le champ pokemon
    def clean_pokemons(self):
        pokemons = self.cleaned_data.get('pokemons')
        user = self.cleaned_data.get('user')
        
        if pokemons:
            # Max 5 Pokémon
            if pokemons.count() > 5:
                raise ValidationError("Une équipe ne peut pas avoir plus de 5 Pokémon.")
            
            # Tous les Pokémon sont à l'utilisateur
            if user:
                for pokemon in pokemons:
                    if pokemon.user != user:
                        raise ValidationError(f"Le Pokémon '{pokemon.name}' n'appartient pas à {user.username}.")
        
        return pokemons

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    form = TeamAdminForm  # Formulaire qui surveille l'ajout de pokemons
    list_display = ("name", "user", "position", "pokemon_count", "is_complete")
    list_filter = ("user", "position")
    search_fields = ("name", "user__username")
    filter_horizontal = ("pokemons",) # pour la gestion des pokemons dans l'équipe
    

    # Methode pour definir les colonnes pokemon_count et is_complete
    def pokemon_count(self, obj):
        return obj.pokemons.count()
    pokemon_count.short_description = "Nombre de Pokémon"
    
    def is_complete(self, obj):
        if obj.is_ready_for_battle():
            return "✅"
        else:
            return "❌"
    is_complete.short_description = "Prête pour combat"
