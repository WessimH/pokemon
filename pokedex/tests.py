from django.contrib.auth.models import User
from django.test import TestCase

from .forms import TeamCreationForm
from .models import PokemonCapture, Team


class TeamTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.pokemons = []
        # Créer 6 pokémons
        for i in range(6):
            p = PokemonCapture.objects.create(
                user=self.user, pokemon_id=i + 1, name=f"Pokemon {i+1}"
            )
            self.pokemons.append(p)

    def test_team_creation_form_valid(self):
        """Test qu'une équipe est valide avec exactement 5 pokémons"""
        data = {
            "name": "Team A",
            "pokemons": [p.id for p in self.pokemons[:5]],  # On en prend 5
        }
        form = TeamCreationForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())
        team = form.save(commit=False)
        team.user = self.user
        team.save()
        form.save_m2m()
        self.assertEqual(team.pokemons.count(), 5)

    def test_team_creation_form_invalid_count(self):
        """Test qu'une équipe échoue si le nombre de pokémons != 5"""
        # Cas avec 4 pokémons
        data_less = {
            "name": "Team Less",
            "pokemons": [p.id for p in self.pokemons[:4]],
        }
        form_less = TeamCreationForm(data=data_less, user=self.user)
        self.assertFalse(form_less.is_valid())
        self.assertIn("Une équipe doit contenir exactement 5 Pokémons.", form_less.errors["pokemons"])

        # Cas avec 6 pokémons
        data_more = {
            "name": "Team More",
            "pokemons": [p.id for p in self.pokemons],  # Tous les 6
        }
        form_more = TeamCreationForm(data=data_more, user=self.user)
        self.assertFalse(form_more.is_valid())
        self.assertIn("Une équipe doit contenir exactement 5 Pokémons.", form_more.errors["pokemons"])

    def test_team_creation_form_wrong_user(self):
        """Test qu'on ne peut pas ajouter les pokémons d'un autre utilisateur"""
        other_user = User.objects.create_user(username="other", password="password")
        other_pokemon = PokemonCapture.objects.create(
            user=other_user, pokemon_id=99, name="Other Pokemon"
        )

        data = {
            "name": "Team Cheater",
            "pokemons": [other_pokemon.id] + [p.id for p in self.pokemons[:4]],
        }
        # Le form filtre le queryset par user, donc other_pokemon ne sera même pas un choix valide
        form = TeamCreationForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        # L'erreur standard Django pour un choix hors queryset est "Select a valid choice..."
        self.assertTrue(form.errors["pokemons"])
