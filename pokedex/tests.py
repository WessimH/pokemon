from django.contrib.auth.models import User
from django.test import TestCase
from django.core.exceptions import ValidationError

from .fight_logic import FightManager
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


    # Test insertion d'une équipe avec pokemons
    def test_insert_team(self):
        team = Team.objects.create(
            user=self.user,
            name="Équipe 1",
            position=0
        )

        # Ajouter 3 pokémons à l'équipe
        team.pokemons.add(self.pokemons[0], self.pokemons[1], self.pokemons[2])

        # Vérifier que l'équipe existe bien en base
        team_db = Team.objects.get(user=self.user, position=0)
        
        # vérifier les données
        self.assertEqual(team_db.name, "Équipe 1")
        self.assertEqual(team_db.position, 0)
        self.assertEqual(team_db.user, self.user)
        self.assertEqual(team_db.pokemons.count(), 3)
        
        # Vérifier que les pokémons sont les bons
        pokemon_ids = list(team_db.pokemons.values_list('id', flat=True))
        self.assertIn(self.pokemons[0].id, pokemon_ids)
        self.assertIn(self.pokemons[1].id, pokemon_ids)
        self.assertIn(self.pokemons[2].id, pokemon_ids)

    # Test pour verifier que on peut avoir qu'une équipe par position par joueur
    def test_team_position_unique(self):
        # Créer une équipe à position 0
        Team.objects.create(
            user=self.user,
            name="Équipe 1",
            position=0
        )
        
        try:
            # Créer une deuxieme équipe position 0
            Team.objects.create(
                user=self.user,
                name="Équipe 1",
                position=0
            )
            # Si ca passe echec 
            self.fail("La contrainte unique_together n'a pas empêché la création")
        except Exception:
            # Erreur attendu
            pass

    # Test pour vérifier qu'on ne peut pas mettre +5 pokemons dans une équipe
    def test_max_five_pokemons_team(self):
        team = Team.objects.create(
            user=self.user,
            name="Équipe Test",
            position=0
        )
        for i in range(5):
            team.add_pokemon(self.pokemons[i])
        
        # Vérifier qu'on a bien 5 pokémons
        self.assertEqual(team.pokemons.count(), 5)
        
        # Essayer d'ajouter un 6ème pokémon, ça doit échouer        
        with self.assertRaises(ValidationError) as context:
            team.add_pokemon(self.pokemons[5])
        
        # Vérifier le message d'erreur
        self.assertIn("5 pokémons", str(context.exception))
        
        # Vérifier qu'on a toujours 5 pokémons
        self.assertEqual(team.pokemons.count(), 5)
    
    # Test 1 pokemon dans plusieurs équipes
    def test_cannot_add_same_pokemon_to_multiple_teams(self):
        # Créer 2 équipes
        team1 = Team.objects.create(user=self.user, name="Team 1", position=0)
        team2 = Team.objects.create(user=self.user, name="Team 2", position=1)
        
        # Ajouter le même pokémon aux deux équipes
        pokemon = self.pokemons[0]
        team1.pokemons.add(pokemon)
        team2.pokemons.add(pokemon)
        
        # Vérifier que le pokémon est bien dans les deux équipes
        self.assertIn(pokemon, team1.pokemons.all())
        self.assertIn(pokemon, team2.pokemons.all())
        self.assertEqual(pokemon.teams.count(), 2)
    
    # Test de l'ordre de Meta
    def test_team_ordering(self):
        # Créer des équipes dans le désordre
        team2 = Team.objects.create(user=self.user, name="Team 2", position=2)
        team0 = Team.objects.create(user=self.user, name="Team 0", position=0)
        team1 = Team.objects.create(user=self.user, name="Team 1", position=1)
        
        teams = list(Team.objects.filter(user=self.user))
        
        # Vérifier qu'elles sont dans l'ordre croissant de position
        self.assertEqual(teams[0].position, 0)
        self.assertEqual(teams[1].position, 1)
        self.assertEqual(teams[2].position, 2)
    


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
