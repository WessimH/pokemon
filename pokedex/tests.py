from django.contrib.auth.models import User
from django.test import TestCase

from .fight_logic import FightManager
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
        self.assertIn(
            "Une équipe doit contenir exactement 5 Pokémons.",
            form_less.errors["pokemons"],
        )

        # Cas avec 6 pokémons
        data_more = {
            "name": "Team More",
            "pokemons": [p.id for p in self.pokemons],  # Tous les 6
        }
        form_more = TeamCreationForm(data=data_more, user=self.user)
        self.assertFalse(form_more.is_valid())
        self.assertIn(
            "Une équipe doit contenir exactement 5 Pokémons.",
            form_more.errors["pokemons"],
        )

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
        # Le form filtre le queryset par user,
        # donc other_pokemon ne sera même pas un choix valide
        form = TeamCreationForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        # L'erreur standard Django pour un choix hors queryset est
        # "Select a valid choice..."
        self.assertTrue(form.errors["pokemons"])


class FightTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="u1", password="pw")
        self.user2 = User.objects.create_user(username="u2", password="pw")

        # Team 1
        self.team1 = Team.objects.create(name="Team 1", user=self.user1)
        for i in range(5):
            p = PokemonCapture.objects.create(
                user=self.user1, pokemon_id=i + 1, name=f"P1-{i}", level=10
            )
            self.team1.pokemons.add(p)

        # Team 2
        self.team2 = Team.objects.create(name="Team 2", user=self.user2)
        for i in range(5):
            p = PokemonCapture.objects.create(
                user=self.user2, pokemon_id=i + 10, name=f"P2-{i}", level=10
            )
            self.team2.pokemons.add(p)

    def test_fight_initialization(self):
        manager = FightManager(self.team1, self.team2)
        state = manager.get_state()

        self.assertEqual(state["team1"]["name"], "Team 1")
        self.assertEqual(len(state["team1"]["pokemons"]), 5)
        self.assertEqual(state["turn"], 0)
        self.assertIsNone(state["winner"])

    def test_fight_turn_attack(self):
        manager = FightManager(self.team1, self.team2)

        # HP Initial du P2 actif (index 0)
        p2_hp_start = manager.team2_state[0]["current_hp"]

        # Action Player: Attaque
        manager.execute_turn({"type": "attack"})

        # Vérif tour incrémenté
        self.assertEqual(manager.turn, 1)

        # Vérif dégâts reçus par P2
        p2_hp_end = manager.team2_state[0]["current_hp"]
        self.assertLess(p2_hp_end, p2_hp_start)

        # Vérif P1 a aussi reçu des dégâts (IA attaque toujours)
        p1_hp_start = manager.team1_state[0]["max_hp"]  # Suppose full HP au début
        p1_hp_end = manager.team1_state[0]["current_hp"]
        self.assertLess(p1_hp_end, p1_hp_start)

    def test_fight_switch(self):
        manager = FightManager(self.team1, self.team2)

        # Switch vers index 1
        manager.execute_turn({"type": "switch", "index": 1})

        self.assertEqual(manager.active_p1, 1)
        # P2 a attaqué le nouveau pokemon (index 1) qui a pris des dégâts
        # Le pokemon 0 devrait être full life
        # (sauf si first strike logic, mais ici switch est prio)
        self.assertEqual(
            manager.team1_state[0]["current_hp"], manager.team1_state[0]["max_hp"]
        )
        self.assertLess(
            manager.team1_state[1]["current_hp"], manager.team1_state[1]["max_hp"]
        )

    def test_win_condition(self):
        manager = FightManager(self.team1, self.team2)

        # On met tous les pokemons de T2 à 1 HP sauf le dernier
        for p in manager.team2_state:
            p["current_hp"] = 0
            p["fainted"] = True

        # On ressuscite le dernier juste pour le kill
        last_p = manager.team2_state[-1]
        last_p["current_hp"] = 1
        last_p["fainted"] = False
        manager.active_p2 = 4  # Index du dernier

        # Attaque fatale
        manager.execute_turn({"type": "attack"})

        self.assertTrue(last_p["fainted"])
        self.assertEqual(manager.winner, "team1")


class PvpTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="u1", password="pw")
        self.user2 = User.objects.create_user(username="u2", password="pw")
        
        # Team 1
        self.team1 = Team.objects.create(name="Team 1", user=self.user1)
        for i in range(5):
            p = PokemonCapture.objects.create(
                user=self.user1, pokemon_id=i + 1, name=f"P1-{i}", level=10
            )
            self.team1.pokemons.add(p)
            
        # Team 2
        self.team2 = Team.objects.create(name="Team 2", user=self.user2)
        for i in range(5):
            p = PokemonCapture.objects.create(
                user=self.user2, pokemon_id=i + 10, name=f"P2-{i}", level=10
            )
            self.team2.pokemons.add(p)

    def test_pvp_initialization(self):
        manager = FightManager(self.team1, self.team2, mode="pvp")
        self.assertEqual(manager.mode, "pvp")

    def test_pvp_turn_execution(self):
        manager = FightManager(self.team1, self.team2, mode="pvp")
        
        # P1 Attacks, P2 Unknown yet (simulated logic in view handles the wait, 
        # but manager.execute_turn expects p2_action if it's pvp and ready)
        
        # 1. Only P1 action passed (should ideally not happen in full flow
        # but logic allows it)
        manager.execute_turn({"type": "attack"})
        
        # In PvP with only P1 action, P2 (AI) should NOT trigger.
        # But P1 attack logic is generic so P1 attacks P2.
        
        p2_hp_mid = manager.team2_state[0]["current_hp"]
        # P2 took damage
        self.assertLess(p2_hp_mid, manager.team2_state[0]["max_hp"])
        
        # P1 hp should be full because P2 didn't attack (no AI)
        p1_hp_start = manager.team1_state[0]["current_hp"]
        self.assertEqual(p1_hp_start, manager.team1_state[0]["max_hp"])

    def test_pvp_turn_full(self):
        manager = FightManager(self.team1, self.team2, mode="pvp")
        
        p1_hp_start = manager.team1_state[0]["current_hp"]
        p2_hp_start = manager.team2_state[0]["current_hp"]

        # Both attack
        manager.execute_turn({"type": "attack"}, {"type": "attack"})
        
        # Both take damage
        self.assertLess(manager.team1_state[0]["current_hp"], p1_hp_start)
        self.assertLess(manager.team2_state[0]["current_hp"], p2_hp_start)
        # Le form filtre le queryset par user
        # donc other_pokemon ne sera même pas un choix valide
        form = TeamCreationForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        # L'erreur standard Django pour un choix hors queryset
        # est "Select a valid choice..."
        self.assertTrue(form.errors["pokemons"])

    def test_team_edit(self):
        """Test la modification d'une équipe"""
        # Création initiale
        team = Team.objects.create(name="Original Team", user=self.user)
        team.pokemons.set(self.pokemons[:5])

        # Modification : CHANGEMENT DE NOM et de POKEMON
        new_pokemons = [
            self.pokemons[0].id,
            self.pokemons[2].id,
            self.pokemons[3].id,
            self.pokemons[4].id,
            self.pokemons[5].id,
        ]

        data = {
            "name": "Updated Team",
            "pokemons": new_pokemons,
        }
        form = TeamCreationForm(data=data, instance=team, user=self.user)
        self.assertTrue(form.is_valid())
        form.save()
        
        team.refresh_from_db()
        self.assertEqual(team.name, "Updated Team")
        self.assertEqual(team.pokemons.count(), 5)
        self.assertIn(self.pokemons[5], team.pokemons.all())
        self.assertNotIn(self.pokemons[1], team.pokemons.all())

    def test_team_delete(self):
        """Test la suppression d'une équipe"""
        team = Team.objects.create(name="To Delete", user=self.user)
        team.pokemons.set(self.pokemons[:5])
        
        team_id = team.id
        team.delete()
        
        self.assertFalse(Team.objects.filter(id=team_id).exists())
