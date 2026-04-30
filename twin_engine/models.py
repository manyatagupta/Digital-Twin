from django.db import models
from django.contrib.auth.models import User

class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    personality_traits = models.TextField(help_text="e.g., Early bird, Tech enthusiast, Cricket lover")
    favorite_genres = models.JSONField(default=list) # e.g., ["Sci-Fi", "Mystery"]

class PastChoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scenario = models.CharField(max_length=255) # e.g., "Weekend Evening"
    choice_made = models.CharField(max_length=255) # e.g., "Watching Cricket"
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} chose {self.choice_made}"