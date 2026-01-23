#!/usr/bin/env python
# Script pour dev et correction
# Script d'initialisation du superutilisateur root et de ses équipes.
# Exécuté automatiquement au démarrage du conteneur Docker.
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User
from pokedex.models import Team

# Récupérer l'utilisateur root
root_user = User.objects.filter(username="root").first()

if root_user:
    # Créer les 5 équipes si elles n'existent pas déjà
    if not root_user.teams.exists():
        for i in range(5):
            Team.objects.create(
                user=root_user,
                name=f"Équipe {i + 1}",
                position=i
            )
        print("5 équipes créées pour l'utilisateur root")
    else:
        print("Les équipes existent déjà pour root")
else:
    print("Utilisateur root non trouvé")
