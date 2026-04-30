from django.shortcuts import render
from .models import UserPreference, PastChoice
from .forms import PreferenceForm
from .logic import get_digital_twin_prediction

def twin_dashboard(request):
    pref, created = UserPreference.objects.get_or_create(user=request.user)
    prediction = None
    
    if request.method == "POST":
        if 'update_pref' in request.POST:
            form = PreferenceForm(request.POST, instance=pref)
            if form.is_valid():
                form.save()
        elif 'get_prediction' in request.POST:
            scenario = request.POST.get('scenario')
            prediction = get_digital_twin_prediction(request.user, scenario)
            PastChoice.objects.create(user=request.user, scenario=scenario, choice_made=prediction)

    form = PreferenceForm(instance=pref)
    return render(request, 'twin_dashboard.html', {'prediction': prediction, 'form': form})