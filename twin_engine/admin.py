from django.contrib import admin
from .models import UserPreference, PastChoice, TwinSettings

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'diet_preference', 'sleep_cycle')
    search_fields = ('user__username', 'personality_traits')

@admin.register(PastChoice)
class PastChoiceAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario', 'choice_made', 'timestamp')
    search_fields = ('user__username', 'scenario')
    list_filter = ('timestamp',)

@admin.register(TwinSettings)
class TwinSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'bot_nickname', 'tone_level', 'preferred_language')
    search_fields = ('user__username', 'bot_nickname')
    list_filter = ('tone_level', 'preferred_language')
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Twin Identity', {'fields': ('bot_nickname',)}),
        ('Personality', {'fields': ('tone_level', 'preferred_language')}),
        ('Custom Rules', {'fields': ('custom_instructions',)}),
    )

