from django.shortcuts import render
import requests 

# Create your views here.

def index(request):
    
    pokemons = [
        {
            'id': 1, 'name': 'Bulbizarre', 'type': 'Plante', 
            'color': 'green', 'desc': 'Il y a une graine sur son dos.'
        },
        {
            'id': 4, 'name': 'Salamèche', 'type': 'Feu', 
            'color': 'red', 'desc': 'La flamme de sa queue vacille.'
        },
        {
            'id': 7, 'name': 'Carapuce', 'type': 'Eau', 
            'color': 'blue', 'desc': 'Il se cache dans sa carapace.'
        },
        {
            'id': 25, 'name': 'Pikachu', 'type': 'Électrik', 
            'color': 'yellow', 'desc': 'Il stocke de l\'électricité.'
        },
        {
            'id': 150, 'name': 'Mewtwo', 'type': 'Psy', 
            'color': 'purple', 'desc': 'Un Pokémon créé par génétique.'
        },
        {
            'id': 143, 'name': 'Ronflex', 'type': 'Normal', 
            'color': 'gray', 'desc': 'Il ne fait que dormir et manger.'
        },
    ]
    
    return render(request,'pokedex/index.html', {'pokemons': pokemons})
