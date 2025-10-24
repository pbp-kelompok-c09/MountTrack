# views.py
from django.shortcuts import render, get_object_or_404
from .models import Mountain

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