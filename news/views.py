from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required 
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse

from .models import News, ImageNews
from .forms import NewsForm, ImageNewsFormSet


def show_main(request):
    """
    View utama yang menampilkan daftar berita terbaru.
    """
    news_list = News.objects.all().order_by('-published_date')
    context = {
        'news_list': news_list
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

    context = {
        'news': news,
        'images': related_images,
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

    context = {'news_list': news_list}

    return render(request, 'news_list_partial.html', context)