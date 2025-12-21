# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Mountain
from .forms import MountainForm
import json

def mountain_list(request):
    mountains = Mountain.objects.all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        mountains = mountains.filter(name__icontains=search_query)
    
    # Province filter
    selected_province = request.GET.get('province', '')
    if selected_province:
        mountains = mountains.filter(province=selected_province)
    
    # Height range filter
    height_range = request.GET.get('height_range', '')
    if height_range:
        if height_range == '0-1000':
            mountains = mountains.filter(height_mdpl__lt=1000)
        elif height_range == '1000-2000':
            mountains = mountains.filter(height_mdpl__gte=1000, height_mdpl__lt=2000)
        elif height_range == '2000-3000':
            mountains = mountains.filter(height_mdpl__gte=2000, height_mdpl__lt=3000)
        elif height_range == '3000-4000':
            mountains = mountains.filter(height_mdpl__gte=3000)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    mountains = mountains.order_by(sort_by)
    
    # Get unique provinces for filter dropdown
    provinces = Mountain.objects.values_list('province', flat=True).distinct().order_by('province')
    
    context = {
        'mountains': mountains,
        'search_query': search_query,
        'selected_province': selected_province,
        'height_range': height_range,
        'sort_by': sort_by,
        'provinces': provinces,
    }
    return render(request, 'mountain_list.html', context)

def mountain_detail(request, name):
    mountain = get_object_or_404(Mountain, name=name)
    return render(request, 'mountain_detail.html', {'mountain': mountain})

# JSON API Endpoints
def mountain_list_json(request):
    """Return mountain list as JSON for AJAX requests"""
    mountains = Mountain.objects.all()
    
    # Apply filters
    search_query = request.GET.get('search', '')
    if search_query:
        mountains = mountains.filter(name__icontains=search_query)
    
    selected_province = request.GET.get('province', '')
    if selected_province:
        mountains = mountains.filter(province=selected_province)
    
    height_range = request.GET.get('height_range', '')
    if height_range:
        if height_range == '0-1000':
            mountains = mountains.filter(height_mdpl__lt=1000)
        elif height_range == '1000-2000':
            mountains = mountains.filter(height_mdpl__gte=1000, height_mdpl__lt=2000)
        elif height_range == '2000-3000':
            mountains = mountains.filter(height_mdpl__gte=2000, height_mdpl__lt=3000)
        elif height_range == '3000-4000':
            mountains = mountains.filter(height_mdpl__gte=3000)
    
    sort_by = request.GET.get('sort', 'name')
    mountains = mountains.order_by(sort_by)
    
    data = [{
        'id': m.id,
        'name': m.name,
        'height_mdpl': m.height_mdpl,
        'province': m.province,
        'image_url': m.image_url or '',
        'description': m.description[:150] + '...' if len(m.description) > 150 else m.description,
        'slug': m.slug,
        'availability': m.availability,
        'min_book': m.min_book,
        'experience_required': m.experience_required,
    } for m in mountains]
    
    return JsonResponse({'mountains': data, 'count': len(data)})

def mountain_detail_json(request, mountain_id):
    """Return mountain detail as JSON"""
    mountain = get_object_or_404(Mountain, id=mountain_id)
    data = {
        'id': mountain.id,
        'name': mountain.name,
        'url': mountain.url,
        'height_mdpl': mountain.height_mdpl,
        'province': mountain.province,
        'image_url': mountain.image_url or '',
        'description': mountain.description,
        'slug': mountain.slug,
        'availability': mountain.availability,
        'min_book': mountain.min_book,
        'experience_required': mountain.experience_required,
    }
    return JsonResponse(data)

# Login-required views
@login_required(login_url='/accounts/login')
def mountain_create(request):
    """Create a new mountain (staff only)"""
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak memiliki izin untuk menambah gunung.')
        return redirect('mountain_list')
    
    if request.method == 'POST':
        form = MountainForm(request.POST)
        if form.is_valid():
            mountain = form.save()
            messages.success(request, f'Gunung {mountain.name} berhasil ditambahkan!')
            return redirect('mountain_detail', name=mountain.name)
    else:
        form = MountainForm()
    
    return render(request, 'mountain_form.html', {'form': form, 'action': 'Tambah'})

@login_required(login_url='/accounts/login')
def mountain_edit(request, mountain_id):
    """Edit an existing mountain (staff only)"""
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak memiliki izin untuk mengedit gunung.')
        return redirect('mountain_list')
    
    mountain = get_object_or_404(Mountain, id=mountain_id)
    
    if request.method == 'POST':
        form = MountainForm(request.POST, instance=mountain)
        if form.is_valid():
            mountain = form.save()
            messages.success(request, f'Gunung {mountain.name} berhasil diperbarui!')
            return redirect('mountain_detail', name=mountain.name)
    else:
        form = MountainForm(instance=mountain)
    
    return render(request, 'mountain_form.html', {
        'form': form, 
        'action': 'Edit',
        'mountain': mountain
    })

@login_required(login_url='/accounts/login')
@require_POST
def mountain_delete(request, mountain_id):
    """Delete a mountain (staff only)"""
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus gunung.')
        return redirect('mountain_list')
    
    mountain = get_object_or_404(Mountain, id=mountain_id)
    mountain_name = mountain.name
    mountain.delete()
    messages.success(request, f'Gunung {mountain_name} berhasil dihapus!')
    return redirect('mountain_list')

# AJAX endpoints
@login_required(login_url='/accounts/login')
@csrf_exempt
@require_POST
def mountain_create_ajax(request):
    """Create mountain via AJAX (staff only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'status': 'error',
            'message': 'Anda tidak memiliki izin untuk menambah gunung.'
        }, status=403)
    
    try:
        # Try to parse as JSON first
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # If not JSON, try to parse the body as JSON string from form data
            body_str = request.POST.get('data') or request.body.decode('utf-8')
            data = json.loads(body_str)
        
        form = MountainForm(data)
        
        if form.is_valid():
            mountain = form.save()
            return JsonResponse({
                'status': 'success',
                'message': f'Gunung {mountain.name} berhasil ditambahkan!',
                'mountain': {
                    'id': mountain.id,
                    'name': mountain.name,
                    'height_mdpl': mountain.height_mdpl,
                    'province': mountain.province,
                    'image_url': mountain.image_url or '',
                    'slug': mountain.slug,
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Data tidak valid',
                'errors': form.errors
            }, status=400)
    except json.JSONDecodeError as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Invalid JSON format: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required(login_url='/accounts/login')
@csrf_exempt
@require_POST
def mountain_edit_ajax(request, mountain_id):
    """Edit mountain via AJAX (staff only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'status': 'error',
            'message': 'Anda tidak memiliki izin untuk mengedit gunung.'
        }, status=403)
    
    try:
        mountain = get_object_or_404(Mountain, id=mountain_id)
        
        # Try to parse as JSON first
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # If not JSON, try to parse the body as JSON string from form data
            body_str = request.POST.get('data') or request.body.decode('utf-8')
            data = json.loads(body_str)
        
        form = MountainForm(data, instance=mountain)
        
        if form.is_valid():
            mountain = form.save()
            return JsonResponse({
                'status': 'success',
                'message': f'Gunung {mountain.name} berhasil diperbarui!',
                'mountain': {
                    'id': mountain.id,
                    'name': mountain.name,
                    'url': mountain.url,
                    'height_mdpl': mountain.height_mdpl,
                    'province': mountain.province,
                    'image_url': mountain.image_url or '',
                    'description': mountain.description,
                    'slug': mountain.slug,
                    'availability': mountain.availability,
                    'min_book': mountain.min_book,
                    'experience_required': mountain.experience_required,
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Data tidak valid',
                'errors': form.errors
            }, status=400)
    except json.JSONDecodeError as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Invalid JSON format: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required(login_url='/accounts/login')
@csrf_exempt
@require_POST
def mountain_delete_ajax(request, mountain_id):
    """Delete mountain via AJAX (staff only)"""
    if not request.user.is_staff:
        return JsonResponse({
            'status': 'error',
            'message': 'Anda tidak memiliki izin untuk menghapus gunung.'
        }, status=403)
    
    try:
        mountain = get_object_or_404(Mountain, id=mountain_id)
        mountain_name = mountain.name
        mountain.delete()
        return JsonResponse({
            'status': 'success',
            'message': f'Gunung {mountain_name} berhasil dihapus!'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)