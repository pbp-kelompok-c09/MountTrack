# ...existing code...
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import BookingForm
from .models import Booking, Mountain, BookingMember
from django.contrib.auth.decorators import login_required
from userprofile.models import UserProfile

def _build_anggota_fields(form, pax_value):
    anggota_fields = []
    for i in range(pax_value):
        name_field = form[f'anggota_{i}_name'] if f'anggota_{i}_name' in form.fields else None
        age_field = form[f'anggota_{i}_age'] if f'anggota_{i}_age' in form.fields else None
        gender_field = form[f'anggota_{i}_gender'] if f'anggota_{i}_gender' in form.fields else None
        level_field = form[f'anggota_{i}_level'] if f'anggota_{i}_level' in form.fields else None

        anggota_fields.append({
            'name': name_field,
            'age': age_field,
            'gender': gender_field,
            'level': level_field,
        })
    return anggota_fields

@login_required
def booking_view(request, gunung_slug):
    gunung = get_object_or_404(Mountain, slug=gunung_slug)
    user_profile = UserProfile.objects.filter(username=request.user.username).first()

    pax_value = 1
    if request.method == 'POST':
        try:
            pax_value = int(request.POST.get('pax', 1))
        except (TypeError, ValueError):
            pax_value = 1
    else:
        try:
            pax_value = int(request.GET.get('pax', 1))
        except (TypeError, ValueError):
            pax_value = 1

    form = BookingForm(request.POST or None, pax=pax_value)

    if request.method == 'POST' and not any(k.startswith('anggota_0_') for k in request.POST.keys()):
        anggota_fields = _build_anggota_fields(form, pax_value)
        return render(request, 'booking/booking_form.html', {
            'form': form,
            'user_profile': user_profile,
            'gunung': gunung,
            'pax': pax_value,
            'anggota_fields': anggota_fields,
        })

    # Final submission: semua field anggota ada
    if request.method == 'POST':
        if form.is_valid():
            levels = []
            anggota_list = []
            for i in range(pax_value):
                name = form.cleaned_data.get(f'anggota_{i}_name')
                age = form.cleaned_data.get(f'anggota_{i}_age')
                gender = form.cleaned_data.get(f'anggota_{i}_gender')
                level = form.cleaned_data.get(f'anggota_{i}_level')
                levels.append(level)
                anggota_list.append({'name': name, 'age': age, 'gender': gender, 'level': level})

            # logika porter
            porter_needed = False
            if all(l == 'beginner' for l in levels):
                porter_needed = True
            elif any(l == 'beginner' for l in levels) and levels.count('intermediate') >= 2:
                porter_needed = True

            if porter_needed and form.cleaned_data.get('porter_hire') != 'yes':
                form.add_error('porter_hire', 'Booking ini membutuhkan penyewaan porter. Pilih "Ya" untuk melanjutkan.')
                anggota_fields = _build_anggota_fields(form, pax_value)
                return render(request, 'booking/booking_form.html', {
                    'form': form,
                    'user_profile': user_profile,
                    'gunung': gunung,
                    'pax': pax_value,
                    'anggota_fields': anggota_fields,
                })

            booking = Booking.objects.create(
                user=request.user,
                gunung=gunung,
                pax=pax_value,
                levels=levels,
                porter_required=porter_needed
            )

            for i in range(pax_value):
                BookingMember.objects.create(
                    booking=booking,
                    name=form.cleaned_data.get(f'anggota_{i}_name'),
                    age=form.cleaned_data.get(f'anggota_{i}_age'),
                    gender=form.cleaned_data.get(f'anggota_{i}_gender'),
                    level=form.cleaned_data.get(f'anggota_{i}_level')
                )

            # tambahkan gunung ke history userprofile jika profil tersedia
            if user_profile:
                try:
                    user_profile.add_history(gunung)
                except Exception:
                    # jangan crash jika ada masalah, bisa ditangani logging jika perlu
                    pass
            return redirect(reverse('booking:booking_summary', kwargs={'booking_id': booking.id}))

            # # redirect ke halaman history — ganti 'userprofile:history' jika route berbeda
            # try:
            #     return redirect(reverse('userprofile:history'))
            # except Exception:
            #     return redirect('/')  # fallback ke homepage
        else:
            anggota_fields = _build_anggota_fields(form, pax_value)
            return render(request, 'booking/booking_form.html', {
                'form': form,
                'user_profile': user_profile,
                'gunung': gunung,
                'pax': pax_value,
                'anggota_fields': anggota_fields,
            })

    # GET: tampilkan form awal (dengan anggota sesuai pax_value)
    anggota_fields = _build_anggota_fields(form, pax_value)
    return render(request, 'booking/booking_form.html', {
        'form': form,
        'user_profile': user_profile,
        'gunung': gunung,
        'pax': pax_value,
        'anggota_fields': anggota_fields,
    })

@login_required
def booking_summary(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    user_profile = UserProfile.objects.filter(username=booking.user.username).first()

    pax_cost = booking.pax * 500
    porter_fee = 250 if booking.porter_required else 0
    total_cost = pax_cost + porter_fee

    # Mengambil anggota data
    anggota_data = []
    for member in booking.members.all():
        anggota_data.append({
            'name': member.name,
            'age': member.age,
            'gender': member.get_gender_display(),
            'level': member.get_level_display(),
        })

    summary = {
        'gunung': booking.gunung.name if booking.gunung else str(booking.gunung),
        'pax': booking.pax,
        'levels': booking.levels,
        'total_cost': total_cost,
        'porter_required': 'Ya' if booking.porter_required else 'Tidak',
        'anggota_data': anggota_data,  # Mengirim data anggota
        'gunung_image_url': booking.gunung.image_url if booking.gunung else None,
        'porter_fee': porter_fee,
        'pax_cost': pax_cost,
    }

    return render(request, 'booking/booking_summary.html', {
        'booking_summary': summary,
        'user_profile': user_profile,
        'booking': booking,
    })

def home(request):
    return render(request, 'home/index.html') 

@login_required
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    # user_profile = UserProfile.objects.filter(username=request.user.username).first()
    member_data = booking.members.all()
    form = BookingForm(request.POST or None, instance=booking, pax=booking.pax)

    for i, member in enumerate(member_data):
        form.fields[f'anggota_{i}_name'].initial = member.name
        form.fields[f'anggota_{i}_age'].initial = member.age
        form.fields[f'anggota_{i}_gender'].initial = member.gender
        form.fields[f'anggota_{i}_level'].initial = member.level

    if form.is_valid():
        form.save()


        return redirect('booking:booking_summary', booking_id=booking.id)

    return render(request, 'booking/edit_booking.html', {'form': form, 'booking': booking})

@login_required
def all_bookings(request):
    bookings = Booking.objects.filter(user=request.user)  # Mendapatkan semua booking untuk user yang sedang login
    return render(request, 'booking/all_bookings.html', {'bookings': bookings})