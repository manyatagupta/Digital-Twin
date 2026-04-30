from django import forms
from .models import UserPreference

class PreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ['personality_traits', 'diet_preference', 'sleep_cycle']
        
        widgets = {
            'personality_traits': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Jaise: B.Tech student, Cricket fan, Night owl...'
            }),
            'diet_preference': forms.Select(attrs={'class': 'form-control'}),
            'sleep_cycle': forms.Select(attrs={'class': 'form-control'}),
        }