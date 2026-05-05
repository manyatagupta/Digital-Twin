from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import UserPreference, PastChoice
from .forms import PreferenceForm
from .logic import get_digital_twin_prediction

@login_required
def twin_dashboard(request):
    pref, created = UserPreference.objects.get_or_create(user=request.user)
    
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

    form = PreferenceForm(instance=pref)
    return render(request, 'twin_dashboard.html', {'form': form})


# ==========================================
# NAYA REGISTER FUNCTION YAHAN ADD KIYA HAI
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