from django.shortcuts import render
from .logic import get_digital_twin_prediction
from django.contrib.auth.decorators import login_required

# Abhi ke liye hum login wala check hata rahe hain taaki aap asani se test kar sako
def twin_dashboard(request):
    prediction = None
    if request.method == "POST":
        user_scenario = request.POST.get('scenario')
        
        # Humne logic.py mein jo function banaya tha usse call kar rahe hain
        # Dummy user bhej rahe hain testing ke liye
        prediction = get_digital_twin_prediction(request.user, user_scenario)

    return render(request, 'twin_dashboard.html', {'prediction': prediction})