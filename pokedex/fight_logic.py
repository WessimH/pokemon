import random

# Table simplifiée des types (Attaquant -> Défenseur : Multiplicateur)
TYPE_CHART = {
    "fire": {"grass": 2.0, "water": 0.5, "bug": 2.0, "ice": 2.0, "steel": 2.0},
    "water": {"fire": 2.0, "ground": 2.0, "rock": 2.0},
    "grass": {"water": 2.0, "ground": 2.0, "rock": 2.0, "flying": 0.5, "fire": 0.5},
    "electric": {"water": 2.0, "flying": 2.0, "ground": 0.0},
    # ... on peut étendre plus tard
}


class FightManager:
    def __init__(self, team1, team2, session_state=None, mode="pve"):
        self.team1 = team1
        self.team2 = team2
        self.mode = mode

        if session_state:
            self.turn = session_state["turn"]
            self.log = session_state["log"]
            self.winner = session_state["winner"]
            self.team1_state = session_state["team1"]["pokemons"]
            self.team2_state = session_state["team2"]["pokemons"]
            self.active_p1 = session_state["team1"]["active_index"]
            self.active_p2 = session_state["team2"]["active_index"]
            self.mode = session_state.get("mode", "pve")
        else:
            self.turn = 0
            self.log = []
            self.winner = None
            self.team1_state = self._init_team_state(team1)
            self.team2_state = self._init_team_state(team2)
            self.active_p1 = 0
            self.active_p2 = 0

    def _init_team_state(self, team):
        state = []
        for p in team.pokemons.all():
            # Calcul simple des HP max: voir models.py ou formule standard
            # Ici on reprend la formule de capture_detail pour la cohérence
            max_hp = int((p.pokemon_id * 0.1 + p.level) * 3 + 10)  # Formule arbitraire
            # On devrait idéalement appeler l'API pour les stats de base,
            # mais pour l'instant on simule
            # Pour faire mieux, il faudrait stocker les stats de base
            # dans le modèle PokemonCapture

            # SIMPLIFICATION: On met 100 HP par défaut + niveau
            max_hp = 100 + (p.level * 5)

            state.append(
                {
                    "id": p.id,
                    "pokemon_id": p.pokemon_id,  # ID de l'API pour les sprites
                    "name": p.name,
                    "nickname": p.nickname if p.nickname else p.name,
                    "level": p.level,
                    "max_hp": max_hp,
                    "current_hp": max_hp,
                    "fainted": False,
                    # Pour l'instant on fera sans type effectiveness complexe
                    # si pas d'API call
                }
            )
        return state

    def get_state(self):
        """Retourne l'état actuel du combat pour la vue/template"""
        return {
            "turn": self.turn,
            "log": self.log,
            "winner": self.winner,
            "mode": self.mode,
            "team1": {
                "name": self.team1.name,
                "active_index": self.active_p1,
                "pokemons": self.team1_state,
            },
            "team2": {
                "name": self.team2.name,
                "active_index": self.active_p2,
                "pokemons": self.team2_state,
            },
        }

    def execute_turn(self, action_p1, action_p2=None):
        """
        Exécute un tour de combat.
        action_p1: {'type': 'attack'} ou {'type': 'switch', 'index': 1}
        action_p2: IA simple par défaut (attaque toujours)
        """
        if self.winner:
            return

        self.turn += 1
        self.log.append(f"--- Tour {self.turn} ---")

        # 1. Gestion des Switchs (priorité haute)
        if action_p1["type"] == "switch":
            idx = int(action_p1["index"])
            if (
                0 <= idx < len(self.team1_state)
                and not self.team1_state[idx]["fainted"]
            ):
                self.active_p1 = idx
                self.log.append(
                    f"{self.team1.user.username} envoie "
                    f"{self.team1_state[idx]['nickname']} !"
                )
            else:
                self.log.append(f"Switch impossible vers {idx}.")

        if self.mode == "pve":
            # IA: Switch si KO, sinon Attaque
            p2_poke = self.team2_state[self.active_p2]
            if p2_poke["fainted"]:
                # Trouver un vivant
                found = False
                for i, p in enumerate(self.team2_state):
                    if not p["fainted"]:
                        self.active_p2 = i
                        self.log.append(f"L'adversaire envoie {p['nickname']} !")
                        found = True
                        break
                if not found:
                    self.winner = "team1"
                    self.log.append("L'adversaire n'a plus de Pokémon !")
                    return
        elif self.mode == "pvp" and action_p2:
            # Joueur 2
            if action_p2["type"] == "switch":
                idx = int(action_p2["index"])
                if (
                    0 <= idx < len(self.team2_state)
                    and not self.team2_state[idx]["fainted"]
                ):
                    self.active_p2 = idx
                    self.log.append(
                        f"{self.team2.user.username} envoie "
                        f"{self.team2_state[idx]['nickname']} !"
                    )
                else:
                    self.log.append(f"Switch inv. P2 vers {idx}.")

        # 2. Combat (si pas de switch P1 et P1 vivant)
        p1_poke = self.team1_state[self.active_p1]
        p2_poke = self.team2_state[self.active_p2]

        if (
            action_p1["type"] == "attack"
            and not p1_poke["fainted"]
            and not p2_poke["fainted"]
        ):
            # Dégâts P1 -> P2
            dmg = self._calculate_damage(p1_poke, p2_poke)
            p2_poke["current_hp"] = max(0, p2_poke["current_hp"] - dmg)
            self.log.append(
                f"{p1_poke['nickname']} attaque ! {dmg} dégâts à {p2_poke['nickname']}."
            )

            if p2_poke["current_hp"] == 0:
                p2_poke["fainted"] = True
                self.log.append(f"{p2_poke['nickname']} est KO !")
                # Check victoire immédiate P1
                if all(p["fainted"] for p in self.team2_state):
                    self.winner = "team1"
                    self.log.append(f"{self.team1.name} remporte la victoire !")
                    return

        if (
            (
                self.mode == "pve"
                or (self.mode == "pvp" and action_p2 and action_p2["type"] == "attack")
            )
            and not p2_poke["fainted"]
            and not p1_poke["fainted"]
        ):
            dmg = self._calculate_damage(p2_poke, p1_poke)
            p1_poke["current_hp"] = max(0, p1_poke["current_hp"] - dmg)
            self.log.append(
                f"{p2_poke['nickname']} attaque ! {dmg} dégâts à {p1_poke['nickname']}."
            )

            if p1_poke["current_hp"] == 0:
                p1_poke["fainted"] = True
                self.log.append(f"{p1_poke['nickname']} est KO !")

                # Check victoire P2
                if all(p["fainted"] for p in self.team1_state):
                    self.winner = "team2"
                    self.log.append(f"{self.team2.name} remporte la victoire !")

    def _calculate_damage(self, attacker, defender):
        # Formule très simplifiée
        # Dégâts = (Niveau * 2) + random(-5, 5)
        base = attacker["level"] * 2
        variation = random.randint(-5, 5)
        return max(1, base + variation)
