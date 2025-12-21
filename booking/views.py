from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import BookingForm
from .models import Booking, Mountain, BookingMember, Payment
from django.contrib.auth.decorators import login_required
from userprofile.models import UserProfile
from django.http import JsonResponse
import logging
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Booking, BookingMember 
from django.utils import timezone
import uuid
from list_gunung.models import Mountain
from django.utils.dateparse import parse_date
from decimal import Decimal
from datetime import timedelta
from django.forms import ValidationError
from django.views.decorators.csrf import csrf_exempt
import logging

try:
    from list_gunung.models import Mountain
except Exception:
    Mountain = None
    
def _safe_int(v, default=None):
    try:
        if v is None or v == '':
            return default
        return int(v)
    except (TypeError, ValueError):
        return default


def _resolve_profile(profile_id):
    if not profile_id:
        return None
    
    try:
        if isinstance(profile_id, uuid.UUID):
            return UserProfile.objects.get(id=profile_id)
        try:
            uid = uuid.UUID(str(profile_id))
            return UserProfile.objects.get(id=uid)
        except (ValueError, TypeError):
            pass
        return UserProfile.objects.get(id=profile_id)
    except (UserProfile.DoesNotExist, ValueError, ValidationError):
        return None
    
def booking_to_dict(booking: Booking) -> dict:
    return {
        'booking_id': booking.id,
        'gunung_nama': getattr(booking.gunung, 'nama', '') if hasattr(booking, 'gunung') else getattr(booking, 'gunung_nama', '') if hasattr(booking, 'gunung_nama') else '',
        'pax': booking.pax,
        'levels': booking.levels if hasattr(booking, 'levels') else [],  # adapt if stored differently
        'porter_required': bool(booking.porter_required) if hasattr(booking, 'porter_required') else False,
        'created_at': booking.created_at.isoformat() if hasattr(booking, 'created_at') else str(booking.created_at),
        'climbing_date': booking.climbing_date.isoformat() if getattr(booking, 'climbing_date', None) else None,
        'anggota': [
            {
                'name': m.name,
                'age': m.age,
                'gender': m.gender,
                'level': m.level,
            } for m in booking.members.all()  # or booking.bookingmember_set.all()
        ],
    }

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def booking_api_create(request):
    """
    Creates a Booking.

    Accepts:
    - JSON body (Content-Type: application/json) with the payload directly, OR
    - form POST with a 'payload' or 'data' field containing the JSON string.
      This is for compatibility with pbp_django_auth's request.post(url, Map<String,String>)
      which sends form-encoded body.
    """
    logger = logging.getLogger(__name__)
    raw_payload = None
    payload = None

    # 1) Try parse JSON body first (application/json)
    try:
        content_type = request.META.get('CONTENT_TYPE', '') or request.content_type or ''
        logger.debug("booking_api_create called; CONTENT_TYPE=%s; COOKIES=%s; user=%s",
                     content_type, request.COOKIES, getattr(request.user, 'username', None))

        if content_type.lower().startswith('application/json'):
            try:
                raw_payload = request.body.decode('utf-8')
                payload = json.loads(raw_payload) if raw_payload else {}
            except Exception as e:
                logger.debug("Failed parse JSON body: %s", e)
                return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
        else:
            # 2) Try form field 'payload' or 'data'
            raw_payload = request.POST.get('payload') or request.POST.get('data') or None
            if raw_payload:
                try:
                    payload = json.loads(raw_payload)
                except Exception:
                    # maybe the client sent a form-like dict where keys are the fields (unlikely),
                    # but we fail gracefully.
                    logger.debug("Failed parse JSON from POST['payload'] or POST['data']")
                    return JsonResponse({'success': False, 'message': 'Invalid JSON in payload form field'}, status=400)
            else:
                # fallback: maybe client sent normal form fields (gunung_id, pax, anggota[] as repeated)
                # We'll try to construct payload from POST fields if present.
                # Handle simple cases where 'anggota' sent as JSON string in a field.
                # If nothing found, return error.
                if 'gunung_id' in request.POST or 'pax' in request.POST:
                    # build payload from individual POST fields (best-effort)
                    try:
                        payload = {}
                        if 'gunung_id' in request.POST:
                            payload['gunung_id'] = request.POST.get('gunung_id')
                        if 'pax' in request.POST:
                            payload['pax'] = request.POST.get('pax')
                        if 'porter_hire' in request.POST:
                            payload['porter_hire'] = request.POST.get('porter_hire')
                        if 'climbing_date' in request.POST:
                            payload['climbing_date'] = request.POST.get('climbing_date')
                        # anggota may come as a JSON string in field 'anggota'
                        anggota_raw = request.POST.get('anggota') or request.POST.get('anggota_json') or None
                        if anggota_raw:
                            try:
                                payload['anggota'] = json.loads(anggota_raw)
                            except Exception:
                                # give up parsing anggota
                                payload['anggota'] = []
                        else:
                            payload['anggota'] = []
                    except Exception:
                        return JsonResponse({'success': False, 'message': 'Invalid form payload'}, status=400)
                else:
                    return JsonResponse({'success': False, 'message': 'Invalid JSON or missing payload'}, status=400)

    except Exception as e:
        logger.exception("Unexpected error while parsing payload: %s", e)
        return JsonResponse({'success': False, 'message': 'Invalid request payload'}, status=400)

    # At this point "payload" is a dict
    if not isinstance(payload, dict):
        return JsonResponse({'success': False, 'message': 'Payload must be an object'}, status=400)

    # (The rest of your previous logic - unchanged, using 'payload' dict)
    pax = _safe_int(payload.get('pax'), None)
    if pax is None:
        pax = 1

    climbing_date_raw = payload.get('climbing_date')
    climbing_date = parse_date(climbing_date_raw) if climbing_date_raw else None

    anggota = payload.get('anggota', []) or []
    porter_hire = payload.get('porter_hire', 'no')
    gunung_id = payload.get('gunung_id') or payload.get('gunung')

    gunung = None
    if gunung_id and Mountain is not None:
        try:
            gunung = Mountain.objects.get(id=gunung_id)
        except (Mountain.DoesNotExist, ValueError, TypeError):
            gunung = None

    anggota_list = []
    for m in anggota:
        if isinstance(m, dict) and m.get('profile_id'):
            prof = _resolve_profile(m.get('profile_id'))
            if prof:
                anggota_list.append({
                    'name': prof.nama,
                    'age': prof.umur if prof.umur not in [None, ''] else None,
                    'gender': getattr(prof, 'jenis_kelamin', None),
                    'level': getattr(prof, 'category_experience', 'beginner') or 'beginner'
                })
                continue

        age_val = _safe_int(m.get('age'), None) if isinstance(m, dict) else None
        anggota_list.append({
            'name': (m.get('name') if isinstance(m, dict) else str(m)) or '',
            'age': age_val,
            'gender': m.get('gender') if isinstance(m, dict) else None,
            'level': m.get('level') if isinstance(m, dict) else 'beginner'
        })

    try:
        user_profile = UserProfile.objects.get(username=request.user.username)
        user_member = {
            'name': user_profile.nama,
            'age': user_profile.umur if user_profile.umur not in [None, ''] else None,
            'gender': getattr(user_profile, 'jenis_kelamin', None),
            'level': getattr(user_profile, 'category_experience', 'beginner') or 'beginner'
        }
    except Exception:
        user_member = {'name': request.user.username, 'age': None, 'gender': None, 'level': 'beginner'}

    if not any(a.get('name') == user_member['name'] for a in anggota_list):
        anggota_list.insert(0, user_member)

    total_pax = max(1, len(anggota_list))
    # derive levels and porter logic
    levels = [m.get('level') or 'beginner' for m in anggota_list]
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
        pax=total_pax,
        levels=levels,
        porter_required=porter_needed,
        climbing_date=climbing_date
    )

    # create members
    for m in anggota_list:
        BookingMember.objects.create(
            booking=booking,
            name=m.get('name') or '',
            age=m.get('age') if m.get('age') not in [None, ''] else None,
            gender=m.get('gender') or None,
            level=m.get('level') or 'beginner',
        )

    return JsonResponse({'success': True, 'booking_id': booking.id, 'message': 'Booking created'}, status=201)


@login_required
@require_http_methods(["POST"])
def booking_api_pay(request, booking_id):
   
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Booking not found'}, status=404)
    if booking.user != request.user:
        return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)

    # try:
    #     payload = json.loads(request.body.decode('utf-8'))
    # except Exception:
    #     payload = {}

   
    pax_cost = booking.pax * 500
    porter_fee = 250 if booking.porter_required else 0
    total_cost = pax_cost + porter_fee

    qris_payload = {
        "qris_id": str(uuid.uuid4()),
        "amount": float(total_cost),
        "message": f"Dummy QRIS for booking {booking.id}"
    }
    payment = Payment.objects.create(
        booking=booking,
        amount=Decimal(total_cost),
        status='pending',
        qris_payload=json.dumps(qris_payload)
    )

    return JsonResponse({
        'success': True,
        'payment_id': payment.id,
        'qris_payload': qris_payload,
        'amount': float(total_cost)
    }, status=201)


@login_required
@require_http_methods(["GET"])
def profiles_api_list(request):

    q = request.GET.get('search')
    if q:
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)
        users = UserProfile.objects.filter(username__icontains=q)[:20]
    else:
        users = UserProfile.objects.filter(id=request.user.id)

    data = []
    for p in users:
            data.append({
                "profile_id": str(p.id),
                "username": p.username,
                "name": p.nama or p.username,
                "age": p.umur,
                "gender": p.jenis_kelamin,
                "level": p.category_experience,
            })
    return JsonResponse({'success': True, 'profiles': data}, status=200)

@login_required
@require_http_methods(["GET"])
def booking_api_detail(request, booking_id):
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

    pax =_safe_int(payload.get('pax'), booking.pax)
    climbing_date_raw = payload.get('climbing_date')
    if climbing_date_raw:
        d = parse_date(climbing_date_raw)
        if d:
            booking.climbing_date = d
    anggota = payload.get('anggota', None)
    porter_hire = payload.get('porter_hire', 'no')
    gunung_id = payload.get('gunung_id') or payload.get('gunung')

    if gunung_id and Mountain is not None:
        try:
            booking.gunung = Mountain.objects.get(id=gunung_id)
        except Exception:
            pass

    # validate porter logic if anggota present
    if anggota is not None:
        anggota_list = []
        for m in anggota:
            if isinstance(m, dict) and m.get('profile_id'):
                prof = _resolve_profile(m.get('profile_id'))
                if prof:
                    anggota_list.append({
                        'name': prof.nama,
                        'age': prof.umur if prof.umur not in [None, ''] else None,
                        'gender': getattr(prof, 'jenis_kelamin', None),
                        'level': getattr(prof, 'category_experience', 'beginner') or 'beginner'
                    })
                    continue
            age_val = _safe_int(m.get('age'), None) if isinstance(m, dict) else None
            anggota_list.append({
                'name': (m.get('name') if isinstance(m, dict) else str(m)) or '',
                'age': age_val,
                'gender': m.get('gender') if isinstance(m, dict) else None,
                'level': m.get('level') if isinstance(m, dict) else 'beginner'
            })

        # ensure user is included
        try:
            user_profile = UserProfile.objects.get(username=request.user.username)
            user_name = user_profile.nama
        except Exception:
            user_name = request.user.username
        if not any(a.get('name') == user_name for a in anggota_list):
            anggota_list.insert(0, {'name': user_name, 'age': None, 'gender': None, 'level': 'beginner'})

        levels = [m.get('level') for m in anggota]
        porter_needed = False
        if levels and all(l == 'beginner' for l in levels):
            porter_needed = True
        elif any(l == 'beginner' for l in levels) and levels.count('intermediate') >= 2:
            porter_needed = True

        if porter_needed and porter_hire != 'yes':
            return JsonResponse({'success': False, 'message': 'Booking requires porter_hire=yes'}, status=400)
        
        booking.pax = max(pax, len(anggota_list))
        booking.levels = levels
        booking.porter_required = porter_needed
        booking.save()

        booking.members.all().delete()
        for m in anggota_list:
            BookingMember.objects.create(
                booking=booking,
                name=m.get('name') or '',
                age=m.get('age') if m.get('age') not in [None, ''] else None,
                gender=m.get('gender') or None,
                level=m.get('level') or 'beginner'
            )
    else:
        booking.pax = pax
        booking.save()

    return JsonResponse({'success': True, 'booking_id': booking.id, 'message': 'Booking updated'}, status=200)


@login_required
@require_http_methods(["GET"])
def booking_api_history(request):
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
    user_profile = None
    try:
        user_profile = UserProfile.objects.get(username=request.user.username)
    except Exception:
        user_profile = None
    
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
        anggota_fields = []
        for i in range(pax_value):
            anggota_fields.append({
                'name': form[f'anggota_{i}_name'] if f'anggota_{i}_name' in form.fields else None,
                'age': form[f'anggota_{i}_age'] if f'anggota_{i}_age' in form.fields else None,
                'gender': form[f'anggota_{i}_gender'] if f'anggota_{i}_gender' in form.fields else None,
                'level': form[f'anggota_{i}_level'] if f'anggota_{i}_level' in form.fields else None,
            })
        return render(request, 'booking/booking_form.html', {
            'form': form,
            'user_profile': user_profile,
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
            user_gender = getattr(user_profile, 'jenis_kelamin', 'M') if user_profile else 'M'
            user_level = getattr(user_profile, 'category_experience', 'beginner') if user_profile else 'beginner'
            user_name = getattr(user_profile, 'nama', request.user.username) if user_profile else request.user.username
            user_age = getattr(user_profile, 'umur', None) if user_profile else None

            levels.append(user_level)
            anggota_list.append({'name': user_name, 'age': user_age or 0, 'gender': user_gender, 'level': user_level})
            
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
                anggota_fields = []
                for i in range(pax_value):
                    anggota_fields.append({
                        'name': form[f'anggota_{i}_name'] if f'anggota_{i}_name' in form.fields else None,
                        'age': form[f'anggota_{i}_age'] if f'anggota_{i}_age' in form.fields else None,
                        'gender': form[f'anggota_{i}_gender'] if f'anggota_{i}_gender' in form.fields else None,
                        'level': form[f'anggota_{i}_level'] if f'anggota_{i}_level' in form.fields else None,
                    })

                return render(request, 'booking/booking_form.html', {
                    'form': form,
                    'user_profile': user_profile,
                    'pax': pax_value,
                    'anggota_fields': anggota_fields,
                    'mountain_id': mountain_id,
                    'pre_selected_mountain': pre_selected_mountain,
                })

            # Total pax = 1 (user) + additional members
            total_pax = 1 + pax_value

            climbing_date = None
           
            if 'climbing_date' in form.cleaned_data:
                climbing_date = form.cleaned_data.get('climbing_date')
            else:
                raw_date = request.POST.get('climbing_date')
                if raw_date:
                    parsed = parse_date(raw_date)
                    if parsed:
                        climbing_date = parsed
            
            booking = Booking.objects.create(
                user=request.user,
                # gunung=gunung,
                gunung=form.cleaned_data['gunung'],
                pax=total_pax,
                levels=levels,
                porter_required=porter_needed,
                climbing_date=climbing_date
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
            return redirect(reverse('booking:booking_summary', kwargs={'booking_id': booking.id}))

        else:
            anggota_fields = []
            for i in range(pax_value):
                anggota_fields.append({
                    'name': form[f'anggota_{i}_name'] if f'anggota_{i}_name' in form.fields else None,
                    'age': form[f'anggota_{i}_age'] if f'anggota_{i}_age' in form.fields else None,
                    'gender': form[f'anggota_{i}_gender'] if f'anggota_{i}_gender' in form.fields else None,
                    'level': form[f'anggota_{i}_level'] if f'anggota_{i}_level' in form.fields else None,
                })

            return render(request, 'booking/booking_form.html', {
                'form': form,
                'user_profile': user_profile,
                'pax': pax_value,
                'anggota_fields': anggota_fields,
                'mountain_id': mountain_id,
                'pre_selected_mountain': pre_selected_mountain,
            })
    anggota_fields = []
    for i in range(pax_value):
        anggota_fields.append({
            'name': form[f'anggota_{i}_name'] if f'anggota_{i}_name' in form.fields else None,
            'age': form[f'anggota_{i}_age'] if f'anggota_{i}_age' in form.fields else None,
            'gender': form[f'anggota_{i}_gender'] if f'anggota_{i}_gender' in form.fields else None,
            'level': form[f'anggota_{i}_level'] if f'anggota_{i}_level' in form.fields else None,
        })
    return render(request, 'booking/booking_form.html', {
        'form': form,
        'user_profile': user_profile,
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
    
    climbing_end_date = None
    if booking.climbing_date:
        duration = booking.duration or 1
        climbing_end_date = booking.climbing_date + timedelta(days=duration - 1)


    summary = {
        
        'gunung': getattr(booking.gunung, 'nama', getattr(booking.gunung, 'name', 'N/A') if booking.gunung else 'N/A'),
        'pax': booking.pax,
        'total_cost': total_cost,
        'porter_required': 'Ya' if booking.porter_required else 'Tidak',
        'anggota_data': anggota_data,  # Mengirim data anggota
       
        'porter_fee': porter_fee,
        'pax_cost': pax_cost,
        'climbing_date': booking.climbing_date.isoformat() if booking.climbing_date else None,
        'climbing_end_date': climbing_end_date,
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
    if booking.user != request.user:
        return redirect('booking:booking_view')

    member_data = list(booking.members.all())
    # pax in model is total pax
    pax_additional = max(0, booking.pax - 1)
    form = BookingForm(request.POST or None, instance=booking, pax=pax_additional)

    # populate initial fields for members
    for i, member in enumerate(member_data[1:]):  # skip first (user) for additional fields
        idx = i
        key_name = f'anggota_{idx}_name'
        key_age = f'anggota_{idx}_age'
        key_gender = f'anggota_{idx}_gender'
        key_level = f'anggota_{idx}_level'
        if key_name in form.fields:
            form.fields[key_name].initial = member.name
        if key_age in form.fields:
            form.fields[key_age].initial = member.age
        if key_gender in form.fields:
            form.fields[key_gender].initial = member.gender
        if key_level in form.fields:
            form.fields[key_level].initial = member.level

    # Populate climbing_date and duration from booking
    if form.fields.get('climbing_date'):
        form.fields['climbing_date'].initial = booking.climbing_date
    if form.fields.get('duration'):
        form.fields['duration'].initial = booking.duration

    if request.method == 'POST' and form.is_valid():
        pax_val = int(request.POST.get('pax', booking.pax))
        anggota_list = []
        
        # keep first member as user (do not overwrite)
        try:
            user_profile = UserProfile.objects.get(username=request.user.username)
            anggota_list.append({
                'name': user_profile.nama,
                'age': user_profile.umur if user_profile.umur not in [None, ''] else None,
                'gender': getattr(user_profile, 'jenis_kelamin', None),
                'level': getattr(user_profile, 'category_experience', 'beginner') or 'beginner'
            })
        except Exception:
            anggota_list.append({'name': request.user.username, 'age': None, 'gender': None, 'level': 'beginner'})

        for i in range(pax_val - 1):
            name = form.cleaned_data.get(f'anggota_{i}_name')
            age = form.cleaned_data.get(f'anggota_{i}_age')
            gender = form.cleaned_data.get(f'anggota_{i}_gender')
            level = form.cleaned_data.get(f'anggota_{i}_level')
            anggota_list.append({'name': name, 'age': age, 'gender': gender, 'level': level})

        # validate porter logic
        levels = [m.get('level') or 'beginner' for m in anggota_list]
        porter_needed = False
        if levels and all(l == 'beginner' for l in levels):
            porter_needed = True
        elif any(l == 'beginner' for l in levels) and levels.count('intermediate') >= 2:
            porter_needed = True

        porter_hire = form.cleaned_data.get('porter_hire', 'no')
        if porter_needed and porter_hire != 'yes':
            form.add_error('porter_hire', 'Booking ini membutuhkan penyewaan porter. Pilih "Ya" untuk melanjutkan.')
            return render(request, 'booking/edit_booking.html', {'form': form, 'booking': booking})

        climbing_date = form.cleaned_data.get('climbing_date') or booking.climbing_date
        duration = form.cleaned_data.get('duration') or booking.duration or 1

        booking.pax = max(1, len(anggota_list))
        booking.levels = [m.get('level') for m in anggota_list]
        booking.porter_required = porter_needed
        booking.climbing_date = climbing_date
        booking.duration = duration
        booking.gunung = form.cleaned_data.get('gunung') or booking.gunung
        booking.save()

        # recreate members
        booking.members.all().delete()
        for m in anggota_list:
            BookingMember.objects.create(
                booking=booking,
                name=m.get('name') or '',
                age=m.get('age') if m.get('age') not in [None, ''] else None,
                gender=m.get('gender') or None,
                level=m.get('level') or 'beginner'
            )
        return redirect('booking:booking_summary', booking_id=booking.id)

    user_profile = UserProfile.objects.filter(username=request.user.username).first()
    anggota_fields = []
    for i in range(pax_additional):
        anggota_fields.append({
            'name': form[f'anggota_{i}_name'] if f'anggota_{i}_name' in form.fields else None,
            'age': form[f'anggota_{i}_age'] if f'anggota_{i}_age' in form.fields else None,
            'gender': form[f'anggota_{i}_gender'] if f'anggota_{i}_gender' in form.fields else None,
            'level': form[f'anggota_{i}_level'] if f'anggota_{i}_level' in form.fields else None,
        })

    return render(request, 'booking/edit_booking.html', {
        'form': form,
        'booking': booking,
        'user_profile': user_profile,
        'pax': pax_additional,
        'anggota_fields': anggota_fields,
    })

@login_required
def all_bookings(request):
    """Halaman riwayat semua booking user."""
    # PENTING: Filter hanya booking milik user yang login
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    # Debug log
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"User {request.user} - Total bookings: {bookings.count()}")
    logger.info(f"Booking IDs: {list(bookings.values_list('id', flat=True))}")
    
    return render(request, 'booking/all_bookings.html', {'bookings': bookings})

@login_required
@require_http_methods(["GET"])
def booking_history_list_plain(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    data = [b.summary() for b in bookings]
    # return list (safe=False) so client gets a plain JSON Array
    return JsonResponse(data, safe=False, status=200)

@login_required
def payment_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.user != request.user:
        return redirect('booking:booking_view')

    # Cek apakah sudah ada payment yang berhasil
    payment = booking.payments.filter(status='paid').first()
    payment_success = payment is not None

    pax_cost = booking.pax * 500000
    porter_fee = 250000 if booking.porter_required else 0
    total_cost = pax_cost + porter_fee

    return render(request, 'booking/payment.html', {
        'booking': booking,
        'total_cost': total_cost,
        'payment_success': payment_success,
    })


logger = logging.getLogger(__name__)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def booking_api_delete(request, booking_id):
    """Delete a booking."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Delete request - booking_id: {booking_id}, user: {request.user}")
    
    # Debug: list semua booking user
    user_bookings = Booking.objects.filter(user=request.user).values_list('id', flat=True)
    logger.info(f"User {request.user} bookings: {list(user_bookings)}")
    
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found for user {request.user}")
        return JsonResponse({
            'success': False, 
            'message': f'Booking {booking_id} tidak ditemukan atau bukan milik Anda'
        }, status=404)
    
    try:
        booking_id_deleted = booking.id
        booking.delete()
        logger.info(f"Booking {booking_id_deleted} deleted successfully")
        return JsonResponse({
            'success': True, 
            'message': 'Booking berhasil dihapus',
            'deleted_id': booking_id_deleted
        }, status=200)
    except Exception as e:
        logger.error(f"Error deleting booking {booking_id}: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        }, status=500)
    
# @login_required
# @require_http_methods(["POST"])
# def booking_api_confirm_payment(request, booking_id):
#     """Confirm payment status untuk booking"""
#     try:
#         booking = Booking.objects.get(id=booking_id)
#     except Booking.DoesNotExist:
#         return JsonResponse({
#             'success': False, 
#             'message': 'Booking tidak ditemukan'
#         }, status=404)
    
#     # Check ownership
#     if booking.user != request.user:
#         return JsonResponse({
#             'success': False, 
#             'message': 'Forbidden - booking bukan milik Anda'
#         }, status=403)
    
#     try:
#         # Parse request body
#         if request.content_type and 'application/json' in request.content_type:
#             payload = json.loads(request.body.decode('utf-8'))
#         else:
#             payload = {
#                 'is_paid': request.POST.get('is_paid'),
#             }
        
#         # Extract is_paid value
#         is_paid_raw = payload.get('is_paid')
#         is_paid = is_paid_raw in [True, 'true', 'True', '1', 1]
        
#         # Update booking
#         booking.is_paid = is_paid
#         booking.save()
        
#         return JsonResponse({
#             'success': True,
#             'booking_id': booking.id,
#             'is_paid': booking.is_paid,
#             'message': 'Payment confirmed'
#         }, status=200)
        
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'message': f'Error: {str(e)}'
#         }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def booking_api_payment(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Booking tidak ditemukan'}, status=404)
    
    if booking.user != request.user:
        return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)

    try:
        # Accept both JSON and form data
        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
        else:
            data = request.POST
        
        is_paid = data.get('is_paid', True) in [True, 'true', 'True', '1', 1]
        
        if is_paid:
            booking.is_paid = True
            booking.save()
            
            # TAMBAHAN: Otomatis tambahkan gunung ke riwayat pendakian user
            if booking.gunung and booking.user:
                try:
                    user_profile = UserProfile.objects.get(id=booking.user.id)
                    # Tambah gunung jika belum ada
                    if not user_profile.history_gunung.filter(id=booking.gunung.id).exists():
                        user_profile.history_gunung.add(booking.gunung)
                except UserProfile.DoesNotExist:
                    pass
        
        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'is_paid': booking.is_paid,
            'message': 'Pembayaran berhasil dikonfirmasi'
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        }, status=500)

@login_required
def booking_landing(request):
    return render(request, 'booking/booking_landing.html')