import random

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import generic

from .fight_logic import FightManager
from .forms import ProfileEditForm
from .models import PokemonCapture, Team
from .utils import ENGLISH_TO_FRENCH, FRENCH_TO_ENGLISH, TYPE_TRANSLATIONS


# --- VUE PRINCIPALE : LISTE DES POKÉMONS (PAGE INDEX) ---
def index(request):
    pokemons_to_display = []
    query = request.GET.get("q")  # On récupère la recherche tout de suite

    items_to_process = []

    # ==========================================
    # CAS 1 : C'EST UNE RECHERCHE
    # ==========================================
    if query:
        # On doit charger la liste des 151 pour chercher dedans
        url = "https://pokeapi.co/api/v2/pokemon?limit=151"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                all_results = response.json()["results"]

                query = query.lower().strip()
                search_term = FRENCH_TO_ENGLISH.get(query, query)

                for item in all_results:
                    p_id = item["url"][:-1].split("/")[-1]

                    # On cherche dans le nom ou l'ID
                    if search_term in item["name"] or query == p_id:
                        items_to_process.append(item)

                # On limite à 6 résultats max pour la recherche
                items_to_process = items_to_process[:6]
        except requests.exceptions.RequestException:
            pass

    # ==========================================
    # CAS 2 : C'EST LE MODE "HASARD" (SESSION)
    # ==========================================
    else:
        # Gestion de la session (Mémoire)
        # Si on force "?new=true" OU s'il n'y a rien en mémoire
        if request.GET.get("new") or "random_team_ids" not in request.session:
            random_ids = random.sample(range(1, 152), 4)
            request.session["random_team_ids"] = random_ids
        else:
            random_ids = request.session["random_team_ids"]

        # On construit manuellement la liste des items à traiter à partir des IDs
        # Pas besoin de charger les 151 ici, on a juste besoin des URLs
        for p_id in random_ids:
            items_to_process.append(
                {
                    "url": f"https://pokeapi.co/api/v2/pokemon/{p_id}/",
                    # On ne connait pas encore le nom, on le trouvera dans le détail
                    "name": "loading...",
                }
            )

    # ==========================================
    # ENRICHISSEMENT (Commun aux deux cas)
    # ==========================================
    for item in items_to_process:
        try:
            detail_response = requests.get(item["url"])
            if detail_response.status_code == 200:
                details = detail_response.json()

                poke_id = details["id"]
                type_en = details["types"][0]["type"]["name"]

                # Traduction Type / Couleur
                type_fr, color = TYPE_TRANSLATIONS.get(type_en, (type_en, "gray"))

                # Traduction Nom
                # Note: On prend le nom depuis 'details' car dans le cas 'Session',
                # item['name'] n'est pas fiable.
                name_en = details["name"]
                name_fr = ENGLISH_TO_FRENCH.get(name_en, name_en).capitalize()

                pokemons_to_display.append(
                    {
                        "id": poke_id,
                        "name": name_fr,
                        "color": color,
                        "type": type_fr,
                        "sprite": details["sprites"]["front_default"],
                    }
                )
        except Exception:
            continue

    return render(
        request, "pokedex/index.html", {"pokemons": pokemons_to_display, "query": query}
    )


# --- VUE : LE DETAIL POKEMON SELECTIONNE (PAGE POKEMON) ---
def pokemon_detail(request, pokemon_id):
    # URL 1 : Infos techniques (Poids, stats, sprites...)
    url_pokemon = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    # URL 2 : Infos d'espèce (Noms traduits, descriptions...)
    url_species = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}"

    context = {}

    try:
        # On lance les requêtes
        response_pk = requests.get(url_pokemon)
        response_sp = requests.get(url_species)

        if response_pk.status_code == 200:
            data_pk = response_pk.json()

            # --- RECUPERATION DU NOM FRANCAIS ---
            name_fr = data_pk["name"]  # Valeur par défaut

            if response_sp.status_code == 200:
                data_sp = response_sp.json()
                for name_entry in data_sp["names"]:
                    if name_entry["language"]["name"] == "fr":
                        name_fr = name_entry["name"]
                        break

            # --- TRADUCTION DU TYPE ---
            type_en = data_pk["types"][0]["type"]["name"]
            type_fr, color = TYPE_TRANSLATIONS.get(type_en, (type_en, "gray"))

            # --- TRADUCTION DES STATS (Ajouté pour cohérence) ---
            stat_translations = {
                "hp": "PV",
                "attack": "Attaque",
                "defense": "Défense",
                "special-attack": "Atq. Spé.",
                "special-defense": "Déf. Spé.",
                "speed": "Vitesse",
            }

            stats = []
            for stat in data_pk["stats"]:
                name_en = stat["stat"]["name"]
                name_fr_stat = stat_translations.get(name_en, name_en)
                stats.append({"name": name_fr_stat, "value": stat["base_stat"]})

            current_team = request.session.get("random_team_ids", [])

            # Si Le Pokémon affiché fait partie des 4 élus du hasard
            if pokemon_id in current_team:
                # On trouve à quelle position il est (0, 1, 2 ou 3)
                current_index = current_team.index(pokemon_id)

                # Le précédent : On recule de 1. Le modulo permet de boucler
                prev_id = current_team[(current_index - 1) % 4]

                # Le suivant : On avance de 1. Le modulo permet de boucler
                next_id = current_team[(current_index + 1) % 4]

            # Si C'est un Pokémon hors liste (accès direct ou recherche)
            else:
                # Logique classique (1 -> 2 -> 3...)
                prev_id = pokemon_id - 1 if pokemon_id > 1 else 151
                next_id = pokemon_id + 1 if pokemon_id < 151 else 1
            context = {
                "pokemon": {
                    "id": data_pk["id"],
                    "name": name_fr,
                    "height": data_pk["height"] / 10,
                    "weight": data_pk["weight"] / 10,
                    "type": type_fr,
                    "color": color,
                    "stats": stats,
                    "sprite": data_pk["sprites"]["other"]["official-artwork"][
                        "front_default"
                    ],
                },
                "previous_id": prev_id,
                "next_id": next_id,
            }
    except Exception as e:
        print(f"Erreur API: {e}")
        pass

    return render(request, "pokedex/pokemon.html", context)


# --- VUE INSCRIPTION UTILISATEUR (PAGE SIGNUP)---
class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"
    
    # On créé l'utilisateur puis ses 5 équipes
    def form_valid(self, form):
        response = super().form_valid(form)
        
        for position in range(5):
            Team.objects.create(
                user=self.object,
                name=f"Équipe {position + 1}",
                position=position
            )
        
        return response


# --- VUE CAPTURE POKÉMON (PAGE INDEX et POKEMON) ---
@login_required
def capture_pokemon(request):
    if request.method == "POST":
        pokemon_id = request.POST.get("pokemon_id")
        raw_name = request.POST.get("pokemon_name")

        clean_name = raw_name.capitalize() if raw_name else "Inconnu"

        PokemonCapture.objects.create(
            user=request.user,
            pokemon_id=pokemon_id,
            name=clean_name,
            nickname=clean_name,
        )
    messages.success(request, f"Félicitations ! Vous avez capturé {clean_name} !", extra_tags="capture_pokemon")

    return redirect(request.META.get("HTTP_REFERER", "index"))


# --- VUE DETAIL D'UN POKÉMON CAPTURÉ (PAGE PROFILE) ---
@login_required
def capture_detail(request, capture_id):
    capture = get_object_or_404(PokemonCapture, id=capture_id, user=request.user)

    # --- GESTION DU RENOMMAGE (POST) ---
    if request.method == "POST":
        new_nickname = request.POST.get("nickname")
        if new_nickname:
            capture.nickname = new_nickname
            capture.save()
            return redirect("capture_detail", capture_id=capture.id)

    # --- RÉCUPERATION DES DONNÉES API ---
    url = f"https://pokeapi.co/api/v2/pokemon/{capture.pokemon_id}"
    response = requests.get(url)

    # Valeurs par défaut pour éviter crash si API HS
    stats_display = []
    height_m = 0
    weight_kg = 0
    description = "Pas de description disponible."
    type_fr = "Inconnu"
    color = "gray"

    if response.status_code == 200:
        data = response.json()
        height_m = data["height"] / 10
        weight_kg = data["weight"] / 10

        # --- RECUPERATION TYPE ET COULEUR (C'est ce qui manquait !) ---
        type_en = data["types"][0]["type"]["name"]
        type_fr, color = TYPE_TRANSLATIONS.get(type_en, (type_en, "gray"))

        # --- RÉCUPERATION DE LA DESCRIPTION ---
        species_url = data["species"]["url"]
        species_response = requests.get(species_url)

        if species_response.status_code == 200:
            species_data = species_response.json()
            for entry in species_data["flavor_text_entries"]:
                if entry["language"]["name"] == "fr":
                    description = entry["flavor_text"].replace("\n", " ")
                    break

        # --- CALCUL DES STATS ---
        stat_translations = {
            "hp": ("PV", "bg-green-500"),
            "attack": ("Attaque", "bg-red-500"),
            "defense": ("Défense", "bg-blue-500"),
            "special-attack": ("Atq. Spé.", "bg-pink-500"),
            "special-defense": ("Déf. Spé.", "bg-purple-500"),
            "speed": ("Vitesse", "bg-yellow-400"),
        }

        for s in data["stats"]:
            name_en = s["stat"]["name"]
            base_stat = s["base_stat"]

            # Calculs RPG (formules)
            if name_en == "hp":
                real_value = int(
                    (base_stat * 2 * capture.level) / 100 + capture.level + 10
                )
            else:
                real_value = int((base_stat * 2 * capture.level) / 100 + 5)

            name_fr_stat, color_bar = stat_translations.get(
                name_en, (name_en, "bg-gray-500")
            )
            percent = min((real_value / 300) * 100, 100)

            stats_display.append(
                {
                    "name": name_fr_stat,
                    "value": real_value,
                    "base": base_stat,
                    "color": color_bar,
                    "percent": percent,
                }
            )
            all_user_captures = list(
                PokemonCapture.objects.filter(user=request.user)
                .order_by("-captured_at")
                .values_list("id", flat=True)
            )

    # 2. On trouve l'index du Pokémon actuel
    current_index = all_user_captures.index(capture.id)
    total_captures = len(all_user_captures)

    prev_capture_id = all_user_captures[(current_index - 1) % total_captures]

    next_capture_id = all_user_captures[(current_index + 1) % total_captures]

    return render(
        request,
        "pokedex/capture_detail.html",
        {
            "pokemon": capture,
            "stats": stats_display,
            "height": height_m,
            "weight": weight_kg,
            "description": description,
            "type": type_fr,  # Ajouté pour le template
            "color": color,  # Ajouté pour le template
            "prev_capture_id": prev_capture_id,
            "next_capture_id": next_capture_id,
        },
    )


# --- VUE PROFIL UTILISATEUR (PAGE PROFILE) ---
@login_required
def profile(request):
    captures = PokemonCapture.objects.filter(user=request.user).order_by("-captured_at")
    return render(request, "pokedex/profile.html", {"captures": captures})


# --- VUE RELACHEMENT POKÉMON (PAGE PROFILE) ---
@login_required
def release_pokemon(request, pokemon_id):
    pokemon = get_object_or_404(PokemonCapture, id=pokemon_id, user=request.user)
    pokemon.delete()
    return redirect("profile")


# --- VUE EDITION PROFIL UTILISATEUR (PAGE EDIT_PROFILE) ---
@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, "pokedex/edit_profile.html", {"form": form})


# --- VUE EQUIPES (PAGE TEAMS) ---
@login_required
def team(request):
    user_teams = Team.objects.filter(user=request.user).order_by("position")

    # On affiche la premiere équipe par défaut
    selected_team_position = int(request.GET.get("team", 0))
    selected_team = user_teams.get(position=selected_team_position)
    
    # Actions de modification
    if request.method == "POST":
        action = request.POST.get("action")
        
        # Renommer une équipe
        if action == "rename":
            new_name = request.POST.get("team_name", "").strip()
            if new_name and len(new_name) <= 100:
                old_name = selected_team.name
                selected_team.rename_team(new_name)
                messages.success(request, f"Équipe renommée : {old_name} -> {new_name}", extra_tags="modification_success")
            else:
                messages.error(request, "Nom d'équipe invalide (1-100 caractères requis).", extra_tags="modification_error")
            return redirect(f"/teams/?team={selected_team_position}")
        
        # Ajouter un pokemon
        elif action == "add_pokemon":
            pokemon_capture_id = request.POST.get("pokemon_id") # Id BDD pas num de pokemon 
            
            try:
                pokemon = PokemonCapture.objects.get(
                    id=pokemon_capture_id, 
                    user=request.user
                )
                
                # Vérifier que l'équipe n'a pas déjà 5 Pokémon
                if selected_team.pokemons.count() >= 5:
                    messages.error(request, f"{selected_team.name} a déjà 5 Pokémons", extra_tags="add_in_full_team")
                
                # Vérifier que le Pokémon est pas déjà dans l'équipe
                elif selected_team.pokemons.filter(id=pokemon.id).exists():
                    messages.warning(request, f"ℹ{pokemon.nickname} est déjà dans cette équipe !", extra_tags="modification_error")
                
                else:
                    selected_team.add_pokemon(pokemon)
                    messages.success(request, f"{pokemon.nickname} a rejoint {selected_team.name} !", extra_tags="add_in_team")
            except PokemonCapture.DoesNotExist:
                messages.error(request, "Ce Pokémon n'existe pas ou ne vous appartient pas.", extra_tags="modification_error")
            
            return redirect(f"/teams/?team={selected_team_position}")
        
        # supprimer un pokemon de l'équipe
        elif action == "remove_pokemon":
            pokemon_capture_id = request.POST.get("pokemon_id")
            
            try:
                pokemon = selected_team.pokemons.get(id=pokemon_capture_id)
                selected_team.pokemons.remove(pokemon)
                messages.success(request, f"{pokemon.nickname} a quitté l'équipe.", extra_tags="remove_from_team")
                
            except PokemonCapture.DoesNotExist:
                messages.error(request, "Impossible de retirer ce Pokémon.", extra_tags="modification_error")
            
            return redirect(f"/teams/?team={selected_team_position}")
    
    # Récupérer les pokémon de l'équipe sélectionnée
    team_pokemons = selected_team.pokemons.all()
    
    # Récupérer les autres
    available_pokemons = PokemonCapture.objects.filter(user=request.user).exclude(
        teams=selected_team
    )
    
    context = {
        "teams": user_teams,
        "selected_team": selected_team,
        "selected_team_position": selected_team_position,
        "team_pokemons": team_pokemons,
        "available_pokemons": available_pokemons,
    }
    
    return render(request, "pokedex/teams.html", context)




# --- VUE COMBATS (PAGE FIGHTS) ---
@login_required
def fight(request):
    # 1. GESTION ACTIONS (POST)
    if request.method == "POST":
        action_type = request.POST.get("action_type")

        # --- START FIGHT ---
        if action_type == "start":
            mode = request.POST.get("mode", "pve")
            team1_id = request.POST.get("team1_id")

            # Vérifier que team1_id existe
            if not team1_id:
                messages.warning(request, "Veuillez sélectionner une équipe complète pour le Joueur 1.", extra_tags="impossible_battle")
                return redirect("fight")

            # Team 1 (Toujours celle du joueur)
            try:
                t1 = Team.objects.get(id=team1_id, user=request.user)
            except Team.DoesNotExist:
                messages.error(request, "Équipe introuvable.", extra_tags="impossible_battle")
                return redirect("fight")
            
            # l'équipe doit avoir exactement 5 Pokémons
            if not t1.is_ready_for_battle():
                messages.error(request, f"'{t1.name}' n'a pas assez de Pokemons pour combattre.", extra_tags="impossible_battle")
                return redirect("fight")

            if mode == "pvp":
                team2_id = request.POST.get("team2_id")
                
                # Vérifier que team2_id existe
                if not team2_id:
                    messages.warning(request, "Veuillez sélectionner une équipe complète pour le Joueur 2.", extra_tags="impossible_battle")
                    return redirect("fight")
                
                # Pour le multi local, on autorise de prendre une autre équipe
                # du même user ou une équipe d'un autre (si on veut).
                # Restons sur user teams pour simplifier l'UI.
                try:
                    t2 = Team.objects.get(id=team2_id)
                except Team.DoesNotExist:
                    messages.error(request, "Équipe 2 introuvable.", extra_tags="impossible_battle")
                    return redirect("fight")
                
                # L'équipe 2 doit aussi avoir exactement 5 Pokémons
                if not t2.is_ready_for_battle():
                    messages.error(request, f"'{t2.name}' n'a pas assez de Pokemons pour combattre.", extra_tags="impossible_battle")
                    return redirect("fight")

                manager = FightManager(t1, t2, mode="pvp")
                request.session["fight_input_phase"] = "p1"  # P1 commence
            else:
                # PVE: Adversaire aléatoire
                others = Team.objects.exclude(id=team1_id)
                # Filtrer uniquement les équipes prêtes pour le combat
                ready_teams = [team for team in others if team.is_ready_for_battle()]
                
                if ready_teams:
                    t2 = random.choice(ready_teams)
                else:
                    t2 = t1  # Mirror match fallback

                manager = FightManager(t1, t2, mode="pve")

            # Sauvegarde en session
            request.session["fight_state"] = manager.get_state()
            request.session["fight_teams"] = {"p1": t1.id, "p2": t2.id}

            return redirect("fight")

        # --- COMBAT ACTION ---
        elif action_type == "turn":
            state = request.session.get("fight_state")
            team_ids = request.session.get("fight_teams")

            if state and team_ids:
                # On recharge les objets Team
                t1 = get_object_or_404(Team, id=team_ids["p1"])
                t2 = get_object_or_404(Team, id=team_ids["p2"])

                manager = FightManager(t1, t2, session_state=state)

                # Parsing de l'action reçue
                move = request.POST.get("move")
                action = {"type": "attack"}
                if move and move.startswith("switch_"):
                    idx = int(move.split("_")[1])
                    action = {"type": "switch", "index": idx}

                # Logique selon le mode
                if manager.mode == "pve":
                    # Execution directe (P1 vs IA)
                    manager.execute_turn(action)
                    request.session["fight_state"] = manager.get_state()

                elif manager.mode == "pvp":
                    phase = request.session.get("fight_input_phase", "p1")

                    if phase == "p1":
                        # On stocke le choix de P1 et on passe à P2
                        request.session["p1_pending_action"] = action
                        request.session["fight_input_phase"] = "p2"

                    elif phase == "p2":
                        # On récupère P1 et on exécute tout
                        p1_action = request.session.get("p1_pending_action")
                        p2_action = action

                        manager.execute_turn(p1_action, p2_action)

                        # Reset pour le prochain tour
                        request.session["fight_state"] = manager.get_state()
                        request.session["fight_input_phase"] = "p1"
                        if "p1_pending_action" in request.session:
                            del request.session["p1_pending_action"]

            return redirect("fight")

        # --- QUIT ---
        elif action_type == "quit":
            keys = [
                "fight_state",
                "fight_teams",
                "fight_input_phase",
                "p1_pending_action",
            ]
            for k in keys:
                if k in request.session:
                    del request.session[k]
            return redirect("fight")

    # 2. AFFICHAGE (GET)
    state = request.session.get("fight_state")

    if state:
        # MODE COMBAT
        input_phase = request.session.get("fight_input_phase", "p1")
        return render(
            request,
            "pokedex/fights.html",
            {"state": state, "in_fight": True, "input_phase": input_phase},
        )
    else:
        # MODE SELECTION
        my_teams = Team.objects.filter(user=request.user)
        return render(
            request, "pokedex/fights.html", {"teams": my_teams, "in_fight": False}
        )
