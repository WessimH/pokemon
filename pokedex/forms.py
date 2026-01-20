from django import forms
from django.contrib.auth.models import User


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {"first_name": "Prénom", "last_name": "Nom", "email": "Adresse E-mail"}

    # Ajout du style Tailwind CSS aux champs du formulaire
    def __init__(self, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {
                    "class": (
                    "w-full border-gray-300 rounded-lg shadow-sm "
                    "focus:border-red-500 focus:ring-red-500 py-2 px-3 text-gray-700"
                    )
                }
            )
