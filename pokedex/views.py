import random

import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import generic

from .fight_logic import FightManager
from .forms import ProfileEditForm, TeamCreationForm
from .models import PokemonCapture, Team
from .utils import ENGLISH_TO_FRENCH, FRENCH_TO_ENGLISH, TYPE_TRANSLATIONS


# --- VUE PRINCIPALE : LISTE DES POKÉMONS (PAGE INDEX) ---
def index(request):
    # Chargement de la liste "légère" des 151 (juste noms + urls)
    url = "https://pokeapi.co/api/v2/pokemon?limit=151"
    pokemons_to_display = []

    try:
        response = requests.get(url)
        if response.status_code == 200:
            all_results = response.json()["results"]

            query = request.GET.get("q")
            filtered_list = []

            if query:
                # --- LOGIQUE RECHERCHE ---
                query = query.lower().strip()

                search_term = FRENCH_TO_ENGLISH.get(query, query)

                for item in all_results:
                    # Recherche par ID
                    p_id = item["url"][:-1].split("/")[-1]

                    if search_term in item["name"] or query == p_id:
                        filtered_list.append(item)

                # 6 premier resultats max
                filtered_list = filtered_list[:6]

            else:
                # --- LOGIQUE HASARD (Index normal) ---
                # 4 pokémons aléatoires
                filtered_list = random.sample(all_results, 4)

            # --- ENRICHISSEMENT (On récupère les types/couleurs) ---
            for item in filtered_list:
                try:
                    # Appel API détail pour CHAQUE résultat
                    detail_response = requests.get(item["url"])
                    if detail_response.status_code == 200:
                        details = detail_response.json()
                        poke_id = details["id"]
                        type_en = details["types"][0]["type"]["name"]

                        type_fr, color = TYPE_TRANSLATIONS.get(
                            type_en, (type_en, "gray")
                        )

                        name_en = item["name"]
                        name_fr = ENGLISH_TO_FRENCH.get(name_en, name_en).capitalize()

                        pokemons_to_display.append(
                            {
                                "id": poke_id,
                                "name": name_fr,
                                "color": color,
                                "type": type_fr,
                            }
                        )
                except Exception:
                    continue

    except requests.exceptions.RequestException:
        pass

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
            # Valeur par défaut (anglais) si l'API species échoue ou si pas de trad
            name_fr = data_pk["name"]

            if response_sp.status_code == 200:
                data_sp = response_sp.json()
                # On cherche 'fr' dans la liste des noms
                for name_entry in data_sp["names"]:
                    if name_entry["language"]["name"] == "fr":
                        name_fr = name_entry["name"]
                        break

            # --- TRADUCTION DU TYPE (Ton code existant) ---
            type_en = data_pk["types"][0]["type"]["name"]
            type_fr, color = TYPE_TRANSLATIONS.get(type_en, (type_en, "gray"))

            # --- LES STATS ---
            stats = []
            for stat in data_pk["stats"]:
                stats.append({"name": stat["stat"]["name"], "value": stat["base_stat"]})

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
                }
            }
    except Exception as e:
        print(f"Erreur API: {e}")  # Utile pour débugger dans ton terminal
        pass

    return render(request, "pokedex/pokemon.html", context)


# --- VUE INSCRIPTION UTILISATEUR (PAGE SIGNUP)---
class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")  # Redirection connexion
    template_name = "registration/signup.html"


# --- VUE CAPTURE POKÉMON (PAGE INDEX et POKEMON) ---
@login_required
def capture_pokemon(request):
    # Post de la capture d'un pokémon
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
            # On recharge la page pour voir le changement
            return redirect("capture_detail", capture_id=capture.id)

    # --- RÉCUPERATION DES DONNÉES API ---
    url = f"https://pokeapi.co/api/v2/pokemon/{capture.pokemon_id}"
    response = requests.get(url)

    stats_display = []
    height_m = 0
    weight_kg = 0
    description = "Pas de description disponible."

    if response.status_code == 200:
        data = response.json()

        # Récupération Taille/Poids (API en décimètres/hectogrammes -> conversion M/KG)
        height_m = data["height"] / 10
        weight_kg = data["weight"] / 10

        # --- RÉCUPERATION DE LA DESCRIPTION (Second appel API) ---
        species_url = data["species"]["url"]
        species_response = requests.get(species_url)

        if species_response.status_code == 200:
            species_data = species_response.json()
            # On cherche la première description en Français
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

            if name_en == "hp":
                real_value = int(
                    (base_stat * 2 * capture.level) / 100 + capture.level + 10
                )
            else:
                real_value = int((base_stat * 2 * capture.level) / 100 + 5)

            name_fr, color = stat_translations.get(name_en, (name_en, "bg-gray-500"))
            percent = min((real_value / 300) * 100, 100)

            stats_display.append(
                {
                    "name": name_fr,
                    "value": real_value,
                    "base": base_stat,
                    "color": color,
                    "percent": percent,
                }
            )

    return render(
        request,
        "pokedex/capture_detail.html",
        {
            "pokemon": capture,
            "stats": stats_display,
            "height": height_m,
            "weight": weight_kg,
            "description": description,
        },
    )


# --- VUE PROFIL UTILISATEUR (PAGE PROFILE) ---
@login_required
def profile(request):
    # Recupération des captures de l'utilisateur connecté
    captures = PokemonCapture.objects.filter(user=request.user).order_by("-captured_at")

    return render(request, "pokedex/profile.html", {"captures": captures})


# --- VUE RELACHEMENT POKÉMON (PAGE PROFILE) ---
@login_required
def release_pokemon(request, pokemon_id):
    # Suppression d'un pokemon capturé
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
            return redirect("profile")  # Retour au profil après sauvegarde
    else:
        # On charge le formulaire avec les infos actuelles de l'utilisateur
        form = ProfileEditForm(instance=request.user)

    return render(request, "pokedex/edit_profile.html", {"form": form})


# --- VUE EQUIPES (PAGE TEAMS) ---
@login_required
def team(request):
    user_teams = Team.objects.filter(user=request.user)

    if request.method == "POST":
        form = TeamCreationForm(request.POST, user=request.user)
        if form.is_valid():
            new_team = form.save(commit=False)
            new_team.user = request.user
            new_team.save()
            # method save_m2m is required for ManyToManyField with commit=False
            form.save_m2m()
            return redirect("team")
    else:
        form = TeamCreationForm(user=request.user)

    return render(request, "pokedex/teams.html", {"teams": user_teams, "form": form})


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
            
            # Team 1 (Toujours celle du joueur)
            t1 = get_object_or_404(Team, id=team1_id, user=request.user)
            
            if mode == "pvp":
                team2_id = request.POST.get("team2_id")
                # Pour le multi local, on autorise de prendre une autre équipe
                # du même user ou une équipe d'un autre (si on veut).
                # Restons sur user teams pour simplifier l'UI.
                t2 = get_object_or_404(Team, id=team2_id)
                
                manager = FightManager(t1, t2, mode="pvp")
                request.session["fight_input_phase"] = "p1" # P1 commence
            else:
                # PVE: Adversaire aléatoire
                others = Team.objects.exclude(id=team1_id)
                if others.exists():
                    t2 = random.choice(list(others))
                else:
                    t2 = t1 # Mirror match fallback

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
            {"state": state, "in_fight": True, "input_phase": input_phase}
        )
    else:
        # MODE SELECTION
        my_teams = Team.objects.filter(user=request.user)
        return render(
            request, "pokedex/fights.html", {"teams": my_teams, "in_fight": False}
        )
