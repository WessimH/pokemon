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


class TeamCreationForm(forms.ModelForm):
    pokemons = forms.ModelMultipleChoiceField(
        queryset=PokemonCapture.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label="Sélectionnez 5 Pokémons",
    )

    class Meta:
        model = Team
        fields = ["name", "pokemons"]
        labels = {"name": "Nom de l'équipe", "pokemons": "Pokémons"}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["pokemons"].queryset = PokemonCapture.objects.filter(user=user)

        style = (
            "w-full border-gray-300 rounded-lg shadow-sm "
            "focus:border-red-500 focus:ring-red-500 py-2 px-3 text-gray-700"
        )
        self.fields["name"].widget.attrs.update({"class": style})

    def clean_pokemons(self):
        pokemons = self.cleaned_data["pokemons"]
        if len(pokemons) != 5:
            raise ValidationError("Une équipe doit contenir exactement 5 Pokémons.")
        return pokemons
