from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Gunung, Booking
from .forms import BookingForm
from userprofile.models import UserProfile
from django.http import HttpResponse

@login_required
def booking_view(request, gunung_id):
    # gunung = get_object_or_404(Gunung, id=gunung_id)  
    user_profile = UserProfile.objects.get(user=request.user)  
    porter_needed = False  
    booking_summary = None  

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            pax = form.cleaned_data['pax']
            levels = form.cleaned_data['levels']
            
            if all(level == 'beginner' for level in levels):  
                porter_needed = True
            elif any(level == 'beginner' for level in levels) and levels.count('intermediate') >= 2: 
                porter_needed = True

            if porter_needed or any(level != 'beginner' for level in levels):  # Booking bisa dilakukan jika ada porter atau tidak semua beginner
                booking = Booking.objects.create(
                    user=request.user,
                    gunung=gunung,
                    pax=pax,
                    levels=levels,
                    porter_required=porter_needed
                )
               
                booking_summary = {
                    'gunung': gunung.nama,
                    'pax': pax,
                    'levels': ', '.join(levels),
                    'porter_required': 'Yes' if porter_needed else 'No',
                }
                return render(request, 'booking/booking_summary.html', {'booking_summary': booking_summary})
        else:
            return HttpResponse("Form is invalid. Please check your input.")

    form = BookingForm()
    return render(request, 'booking/booking_form.html', {'gunung': gunung, 'user_profile': user_profile, 'form': form})
