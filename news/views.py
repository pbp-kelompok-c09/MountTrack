from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required 
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse

from .models import News, ImageNews
from .forms import NewsForm, ImageNewsFormSet
from django.db.models import Q


def show_main(request):
    """
    View utama yang menampilkan daftar berita terbaru.
    """
    news_list = News.objects.all().order_by('-published_date')
    liked_news_ids = []
    if request.user.is_authenticated:
        # Ambil daftar ID berita yang sudah di-like oleh user
        liked_news_ids = request.user.news_likes.values_list('id', flat=True)
    
    context = {
        'news_list': news_list,
        'liked_news_ids': liked_news_ids,
    }
    return render(request, 'page_news.html', context)


@login_required
def create_news(request):
    if request.method == "POST":
        news_form = NewsForm(request.POST)
        image_formset = ImageNewsFormSet(request.POST)

        if news_form.is_valid() and image_formset.is_valid():
            news = news_form.save(commit=False)
            news.user = request.user
            news.save()

            # Hubungkan setiap image ke news yang baru
            for form in image_formset:
                if form.cleaned_data and form.cleaned_data.get('image_url'):
                    image = form.save(commit=False)
                    image.news = news
                    image.save()

            messages.success(request, "Berita berhasil dibuat!")
            return redirect("news:page_news")
        else:
            messages.error(request, "Terdapat kesalahan pada form.")
    else:
        news_form = NewsForm()
        image_formset = ImageNewsFormSet()

    return render(request, "create_news.html", {
        "news_form": news_form,
        "image_formset": image_formset,
        "page_title": "Buat Berita Baru",
    })


def show_news(request, news_id):
    news = get_object_or_404(News, id=news_id)
    news.increment_views()
    related_images = news.images.all()  

    #cek status like
    is_liked = False
    if news.likes.filter(id=request.user.id).exists():
        is_liked = True

    context = {
        'news': news,
        'images': related_images,
        'total_likes': news.total_likes(), # Kirim jumlah like
        'is_liked': is_liked,              # Kirim status (True/False)
    }
    return render(request, 'show_news.html', context)


@staff_member_required(login_url='userprofile:login')
@require_POST
def delete_news(request, news_id):
    """
    View untuk menghapus satu artikel berita.
    """
    news = get_object_or_404(News, id=news_id)
    news.delete()
    messages.success(request, 'Berita berhasil dihapus.')
    return redirect('news:page_news')


@staff_member_required(login_url='userprofile:login')
def edit_news(request, news_id):
    """
    View untuk mengedit instance News yang sudah ada.
    """
    news_instance = get_object_or_404(News, id=news_id)

    if request.method == 'POST':
        news_form = NewsForm(request.POST, instance=news_instance)
        image_formset = ImageNewsFormSet(request.POST, instance=news_instance, prefix='images')

        if news_form.is_valid() and image_formset.is_valid():
            saved_news = news_form.save(commit=False)
            saved_news.user = request.user
            saved_news.save()

            image_formset.instance = saved_news
            image_formset.save()

            messages.success(request, 'Berita berhasil diperbarui (diedit)!')
            return redirect('news:page_news')
        else:
            messages.error(request, 'Gagal mengedit berita. Periksa kembali field yang kosong atau tidak valid.')

    else:  
        news_form = NewsForm(instance=news_instance)
        image_formset = ImageNewsFormSet(instance=news_instance, prefix='images')

    context = {
        'news_form': news_form,
        'image_formset': image_formset,
        'page_title': 'Edit Berita',
    }
    return render(request, 'create_news.html', context)

def search_news(request):
    """
    View ini dipanggil oleh AJAX untuk mencari berita berdasarkan judul.
    Mengembalikan snippet HTML dari daftar berita yang cocok.
    """
    search_term = request.GET.get('q', '') 

    if search_term:
        
        news_list = News.objects.filter(
            title__icontains=search_term
        ).order_by('-published_date')

    else:
        
        news_list = News.objects.all().order_by('-published_date')

    liked_news_ids = []
    if request.user.is_authenticated:
        liked_news_ids = request.user.news_likes.values_list('id', flat=True)
                                                             
    context = {'news_list': news_list,
               'liked_news_ids': liked_news_ids,}

    return render(request, 'news_list_partial.html', context)

@login_required(login_url='userprofile:login')
@require_POST
def like_news(request, news_id):
    news = get_object_or_404(News, id=news_id)
    
    # Toggle Like
    if news.likes.filter(id=request.user.id).exists():
        news.likes.remove(request.user)
        is_liked = False
    else:
        news.likes.add(request.user)
        is_liked = True
    
    # Kembalikan data JSON
    return JsonResponse({
        'status': 'success',
        'is_liked': is_liked,
        'total_likes': news.total_likes()
    })