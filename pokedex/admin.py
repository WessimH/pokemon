from django.contrib import admin

from .models import PokemonCapture

# Register your models here.


# On crée une configuration simple pour l'admin
@admin.register(PokemonCapture)
class PokemonCaptureAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "level", "experience", "captured_at")
    list_filter = ("user", "level")
    search_fields = ("name", "user__username")
