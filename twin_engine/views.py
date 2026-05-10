from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import UserPreference, PastChoice, TwinSettings
from .forms import PreferenceForm, TwinSettingsForm

# Dhyan de: Yahan 'get_ai_debate' import kar liya hai
from .logic import get_digital_twin_prediction, get_system_prompt_with_personality, get_ai_debate

@login_required
def twin_dashboard(request):
    pref, created = UserPreference.objects.get_or_create(user=request.user)
    twin_settings, created = TwinSettings.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        
        # 1. Prediction Handle Karna
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'get_prediction' in request.POST:
            scenario = request.POST.get('scenario')
            prediction = get_digital_twin_prediction(request.user, scenario)
            PastChoice.objects.create(user=request.user, scenario=scenario, choice_made=prediction)
            return JsonResponse({'prediction': prediction})

        # 2. 🔥 NAYA: Debate Mode Handle Karna 🔥
        elif request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'get_debate' in request.POST:
            topic = request.POST.get('topic')
            opponent = request.POST.get('opponent')
            
            # Logic file se debate script mangwa rahe hain
            debate_script = get_ai_debate(request.user, topic, opponent)
            return JsonResponse({'script': debate_script})

        # 3. Preferences Update Karna
        elif 'update_pref' in request.POST:
            form = PreferenceForm(request.POST, instance=pref)
            if form.is_valid():
                form.save()

        # 4. Twin Settings Update Karna
        elif 'update_twin_settings' in request.POST:
            twin_form = TwinSettingsForm(request.POST, instance=twin_settings)
            if twin_form.is_valid():
                twin_form.save()

    form = PreferenceForm(instance=pref)
    twin_form = TwinSettingsForm(instance=twin_settings)
    
    # Spotify Auto-Mood Logic (Fixed playlists, no search hassle)
    mood_map = {
        'Stressed': '37i9dQZF1DWZqd5YICuS7s',
        'Tired': '37i9dQZF1DWZqd5YICuS7s',
        'Motivated': '37i9dQZF1DXdxcBWu9YQL3',
        'Focused': '37i9dQZF1DXdxcBWu9YQL3',
        'Happy': '37i9dQZF1DX3rxVfibe1L0',
        'Chill': '37i9dQZF1DX3rxVfibe1L0',
    }

    playlist_id = mood_map.get(twin_settings.last_mood, '37i9dQZF1DX4WYpdgoIcnm')
    spotify_link = f"https://open.spotify.com/embed/playlist/{playlist_id}?utm_source=generator"

    context = {
        'form': form,
        'twin_form': twin_form,
        'pref': pref,
        'twin_settings': twin_settings,
        'spotify_link': spotify_link,
    }
    return render(request, 'twin_dashboard.html', context)

# ==========================================
# REGISTER FUNCTION
# ==========================================
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) 
            return redirect('twin_dashboard') 
    else:
        form = UserCreationForm()
        
    return render(request, 'registration/register.html', {'form': form})