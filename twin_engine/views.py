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
    twin_settings, twin_created = TwinSettings.objects.get_or_create(user=request.user)
    
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
    
    context = {
        'form': form,
        'twin_form': twin_form,
        'twin_settings': twin_settings,
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