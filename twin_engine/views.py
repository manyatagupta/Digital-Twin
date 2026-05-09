from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import UserPreference, PastChoice, TwinSettings
from .forms import PreferenceForm, TwinSettingsForm
from .logic import get_digital_twin_prediction, get_system_prompt_with_personality

@login_required
def twin_dashboard(request):
    pref, created = UserPreference.objects.get_or_create(user=request.user)
    twin_settings, created = TwinSettings.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'get_prediction' in request.POST:
            scenario = request.POST.get('scenario')
            
            prediction = get_digital_twin_prediction(request.user, scenario)
            
            PastChoice.objects.create(user=request.user, scenario=scenario, choice_made=prediction)
            
            return JsonResponse({'prediction': prediction})

        elif 'update_pref' in request.POST:
            form = PreferenceForm(request.POST, instance=pref)
            if form.is_valid():
                form.save()

        elif 'update_twin_settings' in request.POST:
            twin_form = TwinSettingsForm(request.POST, instance=twin_settings)
            if twin_form.is_valid():
                twin_form.save()

    form = PreferenceForm(instance=pref)
    twin_form = TwinSettingsForm(instance=twin_settings)
    
    # Mood ke hisaab se Spotify ID map karo
    mood_map = {
        'Stressed': '37i9dQZF1DWZqd5YICuS7s', # Lofi
        'Tired': '37i9dQZF1DWZqd5YICuS7s',
        'Motivated': '37i9dQZF1DXdxcBWu9YQL3', # Power
        'Focused': '37i9dQZF1DXdxcBWu9YQL3',
        'Happy': '37i9dQZF1DX3rxVfibe1L0', # Feel Good
        'Chill': '37i9dQZF1DX3rxVfibe1L0',
    }
    
    playlist_id = mood_map.get(twin_settings.last_mood, '37i9dQZF1DX4WYpdgoIcnm') # Default
    
    context = {
        'form': form,
        'twin_form': twin_form,
        'twin_settings': twin_settings,
        'favorite_color': pref.favorite_color,
        'spotify_link': f"https://open.spotify.com/embed/playlist/{playlist_id}"
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