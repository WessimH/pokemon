from django.db import models
from django.contrib.auth.models import User

class PokemonCapture(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='captures')
    
    pokemon_id = models.IntegerField()  # L'ID officiel (ex: 25 pour Pikachu)
    name = models.CharField(max_length=100) # Le nom (ex: "Pikachu" ou "Dracaufeu")
    
    nickname = models.CharField(max_length=100, blank=True, null=True) # Surnom optionnel
    level = models.IntegerField(default=1) # Niveau du Pokémon (commence à 1)
    experience = models.IntegerField(default=0) # Pour monter de niveau plus tard
    
    # Est-ce qu'il est dans l'équipe active (max 6) ?
    in_team = models.BooleanField(default=False) 
    
    captured_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} (Dresseur: {self.user.username})"