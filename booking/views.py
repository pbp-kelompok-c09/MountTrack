# ...existing code...
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import BookingForm
from .models import Booking, Mountain, BookingMember
from django.contrib.auth.decorators import login_required
from userprofile.models import UserProfile
from django.http import JsonResponse
import logging
import json
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.core.exceptions import ObjectDoesNotExist


# logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["POST"])
def booking_api_create(request):
    """
    Create booking from JSON payload:
    {
      "gunung_id": 123,        # optional if you accept 'gunung' name; prefer id
      "pax": 2,
      "anggota": [
         {"name": "A", "age": 30, "gender": "M", "level": "beginner"},
         ...
      ],
      "porter_hire": "yes"  # or "no"
      "climbing_date": "2025-12-01"  # optional (ISO date)
    }
    Response JSON:
    { "success": True, "booking_id": 42, "message": "Created" }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

    pax = int(payload.get('pax', 1))
    anggota = payload.get('anggota', [])
    porter_hire = payload.get('porter_hire', 'no')
    gunung_id = payload.get('gunung_id') or payload.get('gunung')

    # find mountain if provided
    gunung = None
    if gunung_id:
        try:
            gunung = Mountain.objects.get(id=gunung_id)
        except (Mountain.DoesNotExist, ValueError, TypeError):
            gunung = None

    # derive levels and porter logic
    levels = [m.get('level') for m in anggota]
    porter_needed = False
    if levels and all(l == 'beginner' for l in levels):
        porter_needed = True
    elif any(l == 'beginner' for l in levels) and levels.count('intermediate') >= 2:
        porter_needed = True

    if porter_needed and porter_hire != 'yes':
        return JsonResponse({'success': False, 'message': 'Booking requires porter_hire=yes'}, status=400)

    # create booking
    booking = Booking.objects.create(
        user=request.user,
        gunung=gunung,
        pax=pax,
        levels=levels,
        porter_required=porter_needed,
    )

    # create members
    for m in anggota:
        BookingMember.objects.create(
            booking=booking,
            name=m.get('name') or '',
            age=m.get('age') if m.get('age') not in [None, ''] else None,
            gender=m.get('gender') or None,
            level=m.get('level') or 'beginner',
        )

    return JsonResponse({'success': True, 'booking_id': booking.id, 'message': 'Booking created'}, status=201)


@login_required
@require_http_methods(["GET"])
def booking_api_detail(request, booking_id):
    """
    Return booking detail (JSON) for given booking_id, only if owned by request.user.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Booking not found'}, status=404)

    if booking.user != request.user:
        return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)

    return JsonResponse({'success': True, 'booking': booking.summary()}, status=200)


@login_required
@require_http_methods(["PUT", "PATCH", "POST"])
def booking_api_update(request, booking_id):
    """
    Update booking from JSON payload (replace pax, anggota, porter_hire, gunung).
    For simplicity we delete existing members and recreate them from payload.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Booking not found'}, status=404)

    if booking.user != request.user:
        return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

    pax = int(payload.get('pax', booking.pax))
    anggota = payload.get('anggota', None)
    porter_hire = payload.get('porter_hire', 'no')
    gunung_id = payload.get('gunung_id') or payload.get('gunung')

    gunung = booking.gunung
    if gunung_id:
        try:
            gunung = Mountain.objects.get(id=gunung_id)
        except (Mountain.DoesNotExist, ValueError, TypeError):
            gunung = booking.gunung  # fallback

    # validate porter logic if anggota present
    if anggota is not None:
        levels = [m.get('level') for m in anggota]
        porter_needed = False
        if levels and all(l == 'beginner' for l in levels):
            porter_needed = True
        elif any(l == 'beginner' for l in levels) and levels.count('intermediate') >= 2:
            porter_needed = True

        if porter_needed and porter_hire != 'yes':
            return JsonResponse({'success': False, 'message': 'Booking requires porter_hire=yes'}, status=400)

    # apply updates
    booking.gunung = gunung
    booking.pax = pax
    if anggota is not None:
        booking.levels = [m.get('level') for m in anggota]
        booking.porter_required = porter_needed
        booking.save()
        # recreate members
        booking.members.all().delete()
        for m in anggota:
            BookingMember.objects.create(
                booking=booking,
                name=m.get('name') or '',
                age=m.get('age') if m.get('age') not in [None, ''] else None,
                gender=m.get('gender') or None,
                level=m.get('level') or 'beginner',
            )
    else:
        booking.save()

    return JsonResponse({'success': True, 'booking_id': booking.id, 'message': 'Booking updated'}, status=200)


@login_required
@require_http_methods(["GET"])
def booking_api_history(request):
    """
    Return list of Booking.summary() for the authenticated user.
    """
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    data = [b.summary() for b in bookings]
    return JsonResponse({'success': True, 'bookings': data}, status=200)

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
def booking_view(request):
    # gunung = get_object_or_404(Mountain, slug=gunung_slug)
    user_profile = UserProfile.objects.filter(username=request.user.username).first()
    
    # Get mountain_id from URL parameter
    mountain_id = request.GET.get('mountain_id') or request.POST.get('mountain_id')
    pre_selected_mountain = None
    if mountain_id:
        try:
            pre_selected_mountain = Mountain.objects.get(id=mountain_id)
        except Mountain.DoesNotExist:
            pass
    
    # pax_value now represents ADDITIONAL members (not including the user)
    pax_value = 0
    if request.method == 'POST':
        try:
            pax_value = int(request.POST.get('pax', 0))
        except (TypeError, ValueError):
            pax_value = 0
    else:
        try:
            pax_value = int(request.GET.get('pax', 0))
        except (TypeError, ValueError):
            pax_value = 0

    form = BookingForm(request.POST or None, pax=pax_value, initial={'gunung': pre_selected_mountain} if pre_selected_mountain else None)
    if request.method == 'POST' and not any(k.startswith('anggota_0_') for k in request.POST.keys()) and pax_value > 0:
        anggota_fields = _build_anggota_fields(form, pax_value)
        return render(request, 'booking/booking_form.html', {
            'form': form,
            'user_profile': user_profile,
            # 'gunung': gunung,
            'pax': pax_value,
            'anggota_fields': anggota_fields,
            'mountain_id': mountain_id,
            'pre_selected_mountain': pre_selected_mountain,
        })

    # Final submission: semua field anggota ada
    if request.method == 'POST':
        if form.is_valid():
            levels = []
            anggota_list = []
            
            # First, add the logged-in user as the first member
            user_gender = user_profile.jenis_kelamin if user_profile.jenis_kelamin else 'M'
            user_level = user_profile.category_experience if user_profile.category_experience else 'beginner'
            levels.append(user_level)
            anggota_list.append({
                'name': user_profile.nama,
                'age': user_profile.umur or 0,
                'gender': user_gender,
                'level': user_level
            })
            
            # Then add additional members
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
                    # 'gunung': gunung,
                    'pax': pax_value,
                    'anggota_fields': anggota_fields,
                    'mountain_id': mountain_id,
                    'pre_selected_mountain': pre_selected_mountain,
                })

            # Total pax = 1 (user) + additional members
            total_pax = 1 + pax_value
            
            booking = Booking.objects.create(
                user=request.user,
                # gunung=gunung,
                gunung=form.cleaned_data['gunung'],
                pax=total_pax,
                levels=levels,
                porter_required=porter_needed
            )

            # Save user as first member
            BookingMember.objects.create(
                booking=booking,
                name=user_profile.nama,
                age=user_profile.umur or 0,
                gender=user_gender,
                level=user_level
            )
            
            # Save additional members
            for i in range(pax_value):
                BookingMember.objects.create(
                    booking=booking,
                    name=form.cleaned_data.get(f'anggota_{i}_name'),
                    age=form.cleaned_data.get(f'anggota_{i}_age'),
                    gender=form.cleaned_data.get(f'anggota_{i}_gender'),
                    level=form.cleaned_data.get(f'anggota_{i}_level')
                )

            # # tambahkan gunung ke history userprofile jika profil tersedia
            # if user_profile:
            #     try:
            #         user_profile.add_history(gunung)
            #     except Exception:
            #         # jangan crash jika ada masalah, bisa ditangani logging jika perlu
            #         pass
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
                # 'gunung': gunung,
                'pax': pax_value,
                'anggota_fields': anggota_fields,
                'mountain_id': mountain_id,
                'pre_selected_mountain': pre_selected_mountain,
            })

    # GET: tampilkan form awal (dengan anggota sesuai pax_value)
    anggota_fields = _build_anggota_fields(form, pax_value)
    return render(request, 'booking/booking_form.html', {
        'form': form,
        'user_profile': user_profile,
        # 'gunung': gunung,
        'pax': pax_value,
        'anggota_fields': anggota_fields,
        'mountain_id': mountain_id,
        'pre_selected_mountain': pre_selected_mountain,
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
        # 'gunung': booking.gunung.name if booking.gunung else str(booking.gunung),
        'gunung': booking.gunung.name,
        'pax': booking.pax,
        'levels': booking.levels,
        'total_cost': total_cost,
        'porter_required': 'Ya' if booking.porter_required else 'Tidak',
        'anggota_data': anggota_data,  # Mengirim data anggota
        # 'gunung_image_url': booking.gunung.image_url if booking.gunung else None,
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


# @login_required
# def submit_booking(request):

#     if request.method == 'POST':
       
#         form = BookingForm(request.POST)

#         if form.is_valid():
#             logger.info(f"Form cleaned data: {form.cleaned_data}")  # Log cleaned data

#             booking = form.save(commit=False)
#             booking.user = request.user
#             booking.save()

#             pax_value = int(request.POST.get('pax', 1))  # Ambil nilai pax dari POST
#             for i in range(pax_value):
#                 member_name = form.cleaned_data.get(f'anggota_{i}_name')
#                 member_age = form.cleaned_data.get(f'anggota_{i}_age')
#                 member_gender = form.cleaned_data.get(f'anggota_{i}_gender')
#                 member_level = form.cleaned_data.get(f'anggota_{i}_level')

#                 if not all([member_name, member_age, member_gender, member_level]):
#                     logger.error(f"Missing data for member {i}: name={member_name}, age={member_age}, gender={member_gender}, level={member_level}")
#                     return JsonResponse({'success': False, 'errors': form.errors.as_json()})

#                 # Simpan data anggota
#                 BookingMember.objects.create(
#                     booking=booking,
#                     name=member_name,
#                     age=member_age,
#                     gender=member_gender,
#                     level=member_level
#                 )

#             return JsonResponse({
#                 'success': True,
#                 'message': 'Booking Successful',
#                 'redirect_url': reverse('booking:booking_summary', kwargs={'booking_id': booking.id})
#             })
#         else:
#             logger.error(f"Form validation failed: {form.errors}")
#             return JsonResponse({'success': False, 'errors': form.errors.as_json()})

#     return JsonResponse({'success': False, 'message': 'Invalid request'})



@login_required
def all_bookings(request):
    bookings = Booking.objects.filter(user=request.user)  # Retrieve all bookings for the logged-in user
    return render(request, 'booking/all_bookings.html', {'bookings': bookings})