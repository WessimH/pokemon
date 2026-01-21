from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import PokemonCapture, Team


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {"first_name": "Prénom", "last_name": "Nom", "email": "Adresse E-mail"}

    # Ajout du style Tailwind CSS aux champs du formulaire
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        style = (
            "w-full border-gray-300 rounded-lg shadow-sm "
            "focus:border-red-500 focus:ring-red-500 py-2 px-3 text-gray-700"
        )

        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": style})


class TeamEditForm(forms.ModelForm):
    # Formulaire pour renommer l'équipe
    class Meta:
        model = Team
        fields = ["name"]
        labels = {"name": "Nom de l'équipe"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style = (
            "w-full border-gray-300 rounded-lg shadow-sm "
            "focus:border-red-500 focus:ring-red-500 py-2 px-3 text-gray-700"
        )
        self.fields["name"].widget.attrs.update({"class": style})
