from django.contrib.auth.models import User
from django.db import models


class PokemonCapture(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="captures")

    pokemon_id = models.IntegerField()  # L'ID officiel
    name = models.CharField(max_length=100)  # Le nom

    nickname = models.CharField(max_length=100, blank=True, null=True)
    level = models.IntegerField(default=1)  # Niveau du Pokémon (commence à 1)
    experience = models.IntegerField(default=0)

    # Est-ce qu'il est dans l'équipe active (max 6) ?
    in_team = models.BooleanField(default=False)

    captured_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Dresseur: {self.user.username})"

    def gain_experience(self, amount):
        """
        Méthode pour ajouter de l'XP et gérer la montée de niveau automatiquement.
        À utiliser par le module de Combat.
        """
        self.experience += amount

        # Formule simple : Il faut 100 XP * le niveau actuel pour monter
        xp_needed = 100 * self.level

        # On utilise une boucle 'while' au cas où on gagne BEAUCOUP d'XP d'un coup
        leveled_up = False
        while self.experience >= xp_needed:
            self.level += 1
            self.experience -= xp_needed
            xp_needed = 100 * self.level  # Le seuil augmente pour le prochain niveau
            leveled_up = True

        self.save()
        return leveled_up


class Team(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=100)
    pokemons = models.ManyToManyField(PokemonCapture, related_name="teams")

    def __str__(self):
        return f"{self.name} de {self.user.username}"
