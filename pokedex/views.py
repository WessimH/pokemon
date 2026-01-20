import random

import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import generic

from .forms import ProfileEditForm
from .models import PokemonCapture
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
                                "sprite": details["sprites"]["front_default"],
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
        print(f"Erreur API: {e}")
        pass

    return render(request, "pokedex/pokemon.html", context)


# --- VUE INSCRIPTION UTILISATEUR (PAGE SIGNUP)---
class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


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
    return render(request, "pokedex/teams.html")


# --- VUE COMBATS (PAGE FIGHTS) ---
@login_required
def fight(request):
    return render(request, "pokedex/fights.html")
