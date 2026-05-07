from django import forms
from .models import UserPreference, TwinSettings

class PreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ['personality_traits', 'diet_preference', 'sleep_cycle', 'favorite_color']
        
        widgets = {
            'personality_traits': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Jaise: B.Tech student, Cricket fan, Night owl...'
            }),
            'diet_preference': forms.Select(attrs={'class': 'form-control'}),
            'sleep_cycle': forms.Select(attrs={'class': 'form-control'}),
            'favorite_color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Blue, Green, Red...'
            }),
        }


class TwinSettingsForm(forms.ModelForm):
    TONE_CHOICES = [
        (1, '🎩 Professional - Formal & Precise'),
        (2, '😊 Casual - Friendly & Helpful'),
        (3, '😂 Witty - Funny & Charming'),
    ]
    
    tone_level = forms.ChoiceField(choices=TONE_CHOICES, widget=forms.RadioSelect(attrs={
        'class': 'form-check-input'
    }))
    
    class Meta:
        model = TwinSettings
        fields = ['bot_nickname', 'tone_level', 'preferred_language', 'custom_instructions']
        
        widgets = {
            'bot_nickname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apka Digital Twin ka naam (e.g., Ajay AI, Mitra)',
                'maxlength': 50
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-control',
                'choices': [
                    ('Hinglish', 'Hinglish - Hindi + English Mix'),
                    ('Hindi', 'Hindi - Pure Hindi'),
                    ('English', 'English - Pure English'),
                ]
            }),
            'custom_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Kuch extra instructions? (e.g., "Kabhi bhi emoji use mat karna", "Always call me Bhai")'
            }),
        }