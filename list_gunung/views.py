from django.shortcuts import render

def mount(request):
    return render(request, 'mount/index.html')
