from django.shortcuts import render, redirect, get_object_or_404
from .models import News
from .forms import NewsForm, ImageNewsFormSet
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required 
from django.views.decorators.http import require_POST
# Create your views here.

#pebepe
def show_main(request):
    news_list = News.objects.all().order_by('-published_date')
    context = {
        'news_list': news_list
    }
    return render(request, 'page_news.html', context)

@login_required(login_url='userprofile:login')
def create_news(request):
    """
    View untuk membuat instance News baru beserta 
    beberapa instance ImageNews terkait.
    """
    
    if request.method == 'POST':
        # Kita binding data POST ke form utama dan formset
        # Gunakan prefix untuk membedakan formset dari form utama
        news_form = NewsForm(request.POST)
        image_formset = ImageNewsFormSet(request.POST, prefix='images')
        
        if news_form.is_valid() and image_formset.is_valid():
            # 1. Simpan form utama (News)
            #    Kita pakai commit=False agar bisa set relasi sebelum benar-benar disimpan
            #    Tapi karena kita tidak perlu memodifikasi news_instance lebih lanjut
            #    sebelum menyimpan formset, kita bisa langsung save()
            news_instance = news_form.save()
            
            # 2. Set instance formset dengan news yang baru saja dibuat
            image_formset.instance = news_instance
            
            # 3. Simpan formset (semua ImageNews)
            image_formset.save()
            
            # Redirect ke halaman detail berita (misalnya)
            # Pastikan Anda punya URL pattern bernama 'show_news'
            return redirect('news:page_news')
    
    else: # request.method == 'GET'
        # Tampilkan form kosong
        news_form = NewsForm()
        image_formset = ImageNewsFormSet(prefix='images')

    context = {
        'news_form': news_form,
        'image_formset': image_formset
    }
    
    return render(request, 'create_news.html', context)



def show_news(request, news_id):
    """
    View untuk menampilkan satu artikel berita (Detail View).
    'news_id' harus didapat dari URL (misal: /news/<uuid:news_id>/)
    """
    
    # Ambil berita, atau tampilkan 404 jika ID tidak ditemukan
    news = get_object_or_404(News, id=news_id)
    
    # Panggil method untuk menambah jumlah view
    news.increment_views()
    
    # Ambil semua gambar terkait
    # Kita bisa gunakan 'images' karena Anda set related_name='images' di model ImageNews
    related_images = news.images.all()
    
    context = {
        'news': news,
        'images': related_images
    }
    
    # Anda perlu membuat template 'show_news.html'
    return render(request, 'show_news.html', context)

@staff_member_required(login_url='userprofile:login') # Memastikan hanya staf yang bisa
@require_POST  # Memastikan view ini hanya bisa diakses via POST
def delete_news(request, news_id):
    """
    View untuk menghapus satu artikel berita.
    """
    # Ambil berita, atau 404 jika tidak ada
    news = get_object_or_404(News, id=news_id)
    
    # Hapus objek dari database
    news.delete()
    
    # Redirect kembali ke halaman daftar berita
    return redirect('news:page_news')