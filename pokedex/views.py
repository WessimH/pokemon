import random
from django.shortcuts import render, redirect
import requests 
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from .models import PokemonCapture

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

# --- VUE PRINCIPALE : LISTE DES POKÉMONS ---
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
                
                # 12 premier resultats max pour eviter surcharge 
                filtered_list = filtered_list[:12]
            
            else:
                # --- LOGIQUE HASARD (Index normal) ---
                # 6 pokémons aléatoires
                filtered_list = random.sample(all_results, 6)

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

# --- VUE : LE DETAIL POKEMON SELECTIONNE ---
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

def team(request):
    return render(request, 'pokedex/teams.html')

def fight(request):
    return render(request, 'pokedex/fights.html')

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login') # Redirection connexion
    template_name = 'registration/signup.html'

@login_required
def capture_pokemon(request):
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