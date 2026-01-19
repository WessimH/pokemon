import random
from django.shortcuts import get_object_or_404, render, redirect
import requests 
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from .models import PokemonCapture
from .forms import ProfileEditForm

# Dictionnaire pour la traduction des type et couleurs associées 
TYPE_TRANSLATIONS = {
    'grass': ('Plante', 'green'),
    'fire': ('Feu', 'red'),
    'water': ('Eau', 'blue'),
    'electric': ('Électrik', 'yellow'),
    'psychic': ('Psy', 'purple'),
    'normal': ('Normal', 'gray'),
    'ice': ('Glace', 'cyan'),
    'fighting': ('Combat', 'orange'),
    'poison': ('Poison', 'fuchsia'),
    'ground': ('Sol', 'amber'),
    'flying': ('Vol', 'indigo'),
    'bug': ('Insecte', 'lime'),
    'rock': ('Roche', 'stone'),
    'ghost': ('Spectre', 'violet'),
    'dragon': ('Dragon', 'rose'),
    'steel': ('Acier', 'slate'),
    'fairy': ('Fée', 'pink'),
}
# Dictionnaire pour la traduction des noms de Pokémon du français vers l'anglais pour la recherche 
FRENCH_TO_ENGLISH = {
    'bulbizarre': 'bulbasaur', 'herbizarre': 'ivysaur', 'florizarre': 'venusaur',
    'salamèche': 'charmander', 'reptincel': 'charmeleon', 'dracaufeu': 'charizard',
    'carapuce': 'squirtle', 'carabaffe': 'wartortle', 'tortank': 'blastoise',
    'chenipan': 'caterpie', 'chrysacier': 'metapod', 'papilusion': 'butterfree',
    'aspicot': 'weedle', 'coconfort': 'kakuna', 'dardargnan': 'beedrill',
    'roucool': 'pidgey', 'roucoups': 'pidgeotto', 'roucarnage': 'pidgeot',
    'rattata': 'rattata', 'rattatac': 'raticate',
    'piafabec': 'spearow', 'rapasdepic': 'fearow',
    'abo': 'ekans', 'arbok': 'arbok',
    'pikachu': 'pikachu', 'raichu': 'raichu',
    'sabelette': 'sandshrew', 'sablaireau': 'sandslash',
    'nidoran♀': 'nidoran-f', 'nidorina': 'nidorina', 'nidoqueen': 'nidoqueen',
    'nidoran♂': 'nidoran-m', 'nidorino': 'nidorino', 'nidoking': 'nidoking',
    'mélofée': 'clefairy', 'mélodelfe': 'clefable',
    'goupix': 'vulpix', 'feunard': 'ninetales',
    'rondoudou': 'jigglypuff', 'grodoudou': 'wigglytuff',
    'nosferapti': 'zubat', 'nosferalto': 'golbat',
    'mystherbe': 'oddish', 'ortide': 'gloom', 'rafflesia': 'vileplume',
    'paras': 'paras', 'parasect': 'parasect',
    'mimitoss': 'venonat', 'aéromite': 'venomoth',
    'taupiqueur': 'diglett', 'triopikeur': 'dugtrio',
    'miaouss': 'meowth', 'persian': 'persian',
    'psykokwak': 'psyduck', 'akwakwak': 'golduck',
    'férosinge': 'mankey', 'colossinge': 'primeape',
    'caninos': 'growlithe', 'arcanin': 'arcanine',
    'ptitard': 'poliwag', 'têtarte': 'poliwhirl', 'tartard': 'poliwrath',
    'abra': 'abra', 'kadabra': 'kadabra', 'alakazam': 'alakazam',
    'machoc': 'machop', 'machopeur': 'machoke', 'mackogneur': 'machamp',
    'chétiflor': 'bellsprout', 'boustiflor': 'weepinbell', 'empiflor': 'victreebel',
    'tentacool': 'tentacool', 'tentacruel': 'tentacruel',
    'racaillou': 'geodude', 'gravalanch': 'graveler', 'grolem': 'golem',
    'ponyta': 'ponyta', 'galopa': 'rapidash',
    'ramoloss': 'slowpoke', 'flagadoss': 'slowbro',
    'magnéti': 'magnemite', 'magnéton': 'magneton',
    'canarticho': 'farfetchd',
    'doduo': 'doduo', 'dodrio': 'dodrio',
    'otaria': 'seel', 'lamantine': 'dewgong',
    'tadmorv': 'grimer', 'grotadmorv': 'muk',
    'kokiyas': 'shellder', 'crustabri': 'cloyster',
    'fantominus': 'gastly', 'spectrum': 'haunter', 'ectoplasma': 'gengar',
    'onix': 'onix',
    'soporifik': 'drowzee', 'hypnomade': 'hypno',
    'krabby': 'krabby', 'krabboss': 'kingler',
    'voltorbe': 'voltorb', 'électrode': 'electrode',
    'noeunoeuf': 'exeggcute', 'noadkoko': 'exeggutor',
    'osselait': 'cubone', 'ossatueur': 'marowak',
    'kicklee': 'hitmonlee', 'tygnon': 'hitmonchan',
    'excelangue': 'lickitung',
    'smogo': 'koffing', 'smogogo': 'weezing',
    'rhinocorne': 'rhyhorn', 'rhinoféros': 'rhydon',
    'leveinard': 'chansey',
    'saquedeneu': 'tangela',
    'kangourex': 'kangaskhan',
    'hypotrempe': 'horsea', 'hypocéan': 'seadra',
    'poissirène': 'goldeen', 'poissoroy': 'seaking',
    'stari': 'staryu', 'staross': 'starmie',
    'm. mime': 'mr-mime',
    'insécateur': 'scyther',
    'lippoutou': 'jynx',
    'élektek': 'electabuzz',
    'magmar': 'magmar',
    'scarabrute': 'pinsir',
    'tauros': 'tauros',
    'magicarpe': 'magikarp', 'léviator': 'gyarados',
    'lokhlass': 'lapras',
    'métamorph': 'ditto',
    'évoli': 'eevee', 'aquali': 'vaporeon', 'voltali': 'jolteon', 'pyroli': 'flareon',
    'porygon': 'porygon',
    'amonita': 'omanyte', 'amonistar': 'omastar',
    'kabuto': 'kabuto', 'kabutops': 'kabutops',
    'ptéra': 'aerodactyl',
    'ronflex': 'snorlax',
    'artikodin': 'articuno',
    'électhor': 'zapdos',
    'sulfura': 'moltres',
    'minidraco': 'dratini', 'draco': 'dragonair', 'dracolosse': 'dragonite',
    'mewtwo': 'mewtwo',
    'mew': 'mew'
}

# On inverse le dictionnaire : { 'bulbasaur': 'bulbizarre', ... }
ENGLISH_TO_FRENCH = {v: k for k, v in FRENCH_TO_ENGLISH.items()}

# --- VUE PRINCIPALE : LISTE DES POKÉMONS (PAGE INDEX) ---
def index(request):
    # Chargement de la liste "légère" des 151 (juste noms + urls)
    url = 'https://pokeapi.co/api/v2/pokemon?limit=151'
    pokemons_to_display = []
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            all_results = response.json()['results']
            
            query = request.GET.get('q')
            filtered_list = []

            if query:
                # --- LOGIQUE RECHERCHE ---
                query = query.lower().strip()
                
                search_term = FRENCH_TO_ENGLISH.get(query, query)
                
                for item in all_results:
                    # Recherche par ID 
                    p_id = item['url'][:-1].split('/')[-1]
                    
                    if search_term in item['name'] or query == p_id:
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
                    detail_response = requests.get(item['url'])
                    if detail_response.status_code == 200:
                        details = detail_response.json()
                        poke_id = details['id']
                        type_en = details['types'][0]['type']['name']
                        
                        type_fr, color = TYPE_TRANSLATIONS.get(type_en, (type_en, 'gray'))
                        
                        name_en = item['name']
                        name_fr = ENGLISH_TO_FRENCH.get(name_en, name_en).capitalize()
                        
                        pokemons_to_display.append({
                            'id': poke_id,
                            'name': name_fr,
                            'color': color,
                            'type': type_fr,
                        })
                except Exception:
                    continue

    except requests.exceptions.RequestException:
        pass

    return render(request, 'pokedex/index.html', {'pokemons': pokemons_to_display, 'query': query})

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
            name_fr = data_pk['name'] 
            
            if response_sp.status_code == 200:
                data_sp = response_sp.json()
                # On cherche 'fr' dans la liste des noms
                for name_entry in data_sp['names']:
                    if name_entry['language']['name'] == 'fr':
                        name_fr = name_entry['name']
                        break
            
            # --- TRADUCTION DU TYPE (Ton code existant) ---
            type_en = data_pk['types'][0]['type']['name']
            type_fr, color = TYPE_TRANSLATIONS.get(type_en, (type_en, 'gray'))

            # --- LES STATS ---
            stats = []
            for stat in data_pk['stats']:
                stats.append({
                    'name': stat['stat']['name'],
                    'value': stat['base_stat']
                })

            context = {
                'pokemon': {
                    'id': data_pk['id'],
                    'name': name_fr, 
                    'height': data_pk['height'] / 10,
                    'weight': data_pk['weight'] / 10,
                    'type': type_fr,
                    'color': color,
                    'stats': stats,
                    'sprite': data_pk['sprites']['other']['official-artwork']['front_default']
                }
            }
    except Exception as e:
        print(f"Erreur API: {e}") # Utile pour débugger dans ton terminal
        pass
        
    return render(request, 'pokedex/pokemon.html', context)

# --- VUE INSCRIPTION UTILISATEUR (PAGE SIGNUP)---
class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login') # Redirection connexion
    template_name = 'registration/signup.html'

# --- VUE CAPTURE POKÉMON (PAGE INDEX et POKEMON) ---
@login_required
def capture_pokemon(request):
    #Post de la capture d'un pokémon 
    if request.method == 'POST':
        pokemon_id = request.POST.get('pokemon_id')
        raw_name = request.POST.get('pokemon_name')
        
        clean_name = raw_name.capitalize() if raw_name else "Inconnu"

        PokemonCapture.objects.create(
            user=request.user,
            pokemon_id=pokemon_id,
            name=clean_name, 
            nickname=clean_name 
        )
        
    return redirect(request.META.get('HTTP_REFERER', 'index'))

# --- VUE DETAIL D'UN POKÉMON CAPTURÉ (PAGE PROFILE) ---
@login_required
def capture_detail(request, capture_id):
    capture = get_object_or_404(PokemonCapture, id=capture_id, user=request.user)
    
    # --- 1. GESTION DU RENOMMAGE (POST) ---
    if request.method == 'POST':
        new_nickname = request.POST.get('nickname')
        if new_nickname:
            capture.nickname = new_nickname
            capture.save()
            # On recharge la page pour voir le changement
            return redirect('capture_detail', capture_id=capture.id)

    # --- 2. RÉCUPERATION DES DONNÉES API ---
    url = f"https://pokeapi.co/api/v2/pokemon/{capture.pokemon_id}"
    response = requests.get(url)
    
    stats_display = []
    height_m = 0
    weight_kg = 0
    description = "Pas de description disponible."

    if response.status_code == 200:
        data = response.json()
        
        # Récupération Taille/Poids (API en décimètres/hectogrammes -> conversion M/KG)
        height_m = data['height'] / 10
        weight_kg = data['weight'] / 10

        # --- 3. RÉCUPERATION DE LA DESCRIPTION (Second appel API) ---
        # L'URL de l'espèce est donnée dans la première réponse
        species_url = data['species']['url']
        species_response = requests.get(species_url)
        
        if species_response.status_code == 200:
            species_data = species_response.json()
            # On cherche la première description en Français
            for entry in species_data['flavor_text_entries']:
                if entry['language']['name'] == 'fr':
                    description = entry['flavor_text'].replace("\n", " ") # Nettoyage du texte
                    break

        # --- 4. CALCUL DES STATS (Inchangé) ---
        stat_translations = {
            'hp': ('PV', 'bg-green-500'),
            'attack': ('Attaque', 'bg-red-500'),
            'defense': ('Défense', 'bg-blue-500'),
            'special-attack': ('Atq. Spé.', 'bg-pink-500'),
            'special-defense': ('Déf. Spé.', 'bg-purple-500'),
            'speed': ('Vitesse', 'bg-yellow-400'),
        }

        for s in data['stats']:
            name_en = s['stat']['name']
            base_stat = s['base_stat']
            
            if name_en == 'hp':
                real_value = int((base_stat * 2 * capture.level) / 100 + capture.level + 10)
            else:
                real_value = int((base_stat * 2 * capture.level) / 100 + 5)
                
            name_fr, color = stat_translations.get(name_en, (name_en, 'bg-gray-500'))
            percent = min((real_value / 300) * 100, 100)

            stats_display.append({
                'name': name_fr,
                'value': real_value,
                'base': base_stat,
                'color': color,
                'percent': percent
            })

    return render(request, 'pokedex/capture_detail.html', {
        'pokemon': capture,
        'stats': stats_display,
        'height': height_m,
        'weight': weight_kg,
        'description': description
    })

# --- VUE PROFIL UTILISATEUR (PAGE PROFILE) ---
@login_required
def profile(request):
    # Recupération des captures de l'utilisateur connecté
    captures = PokemonCapture.objects.filter(user=request.user).order_by('-captured_at')
    
    return render(request, 'pokedex/profile.html', {'captures': captures})

# --- VUE RELACHEMENT POKÉMON (PAGE PROFILE) ---
@login_required
def release_pokemon(request, pokemon_id):
    # On cherche le pokémon correspondant à l'ID ET à l'utilisateur connecté pour le supprimer
    pokemon = get_object_or_404(PokemonCapture, id=pokemon_id, user=request.user)
    
    pokemon.delete()
    
    return redirect('profile')

# --- VUE EDITION PROFIL UTILISATEUR (PAGE EDIT_PROFILE) ---
@login_required
def edit_profile(request):
    if request.method == 'POST':
        # On charge le formulaire avec les données envoyées (POST) et l'utilisateur actuel (instance)
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile') # Retour au profil après sauvegarde
    else:
        # On charge le formulaire avec les infos actuelles de l'utilisateur
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'pokedex/edit_profile.html', {'form': form})

# --- VUE EQUIPES (PAGE TEAMS) ---
@login_required
def team(request):
    return render(request, 'pokedex/teams.html')

# --- VUE COMBATS (PAGE FIGHTS) ---
@login_required
def fight(request):
    return render(request, 'pokedex/fights.html')