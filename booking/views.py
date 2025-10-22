from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Gunung, Booking
from userprofile.models import UserProfile  
from django.http import HttpResponse

@login_required
def booking_view(request):
    gunungs = Gunung.objects.filter(ketersediaan=True)  
    user_profile = UserProfile.objects.get(user=request.user)  

    if request.method == 'POST':
        pax = int(request.POST['pax'])
        levels = request.POST.getlist('levels')  
        
        porter_required = False
        if all(level == 'beginner' for level in levels):
            porter_required = True
        
        if porter_required or any(level != 'beginner' for level in levels):
            booking = Booking.objects.create(
                user=request.user,
                gunung=Gunung.objects.get(id=request.POST['gunung_id']),
                pax=pax,
                levels=levels,
                porter_required=porter_required
            )
            return HttpResponse(f"Booking successful for {pax} pax!")
        else:
            return HttpResponse("Booking failed. You must rent a porter if all pax are beginners.")
    
    return render(request, 'booking/booking_form.html', {'gunungs': gunungs, 'user_profile': user_profile})
