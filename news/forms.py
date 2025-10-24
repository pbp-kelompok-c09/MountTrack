from django import forms
from django.forms import ModelForm, inlineformset_factory
from news.models import News, ImageNews

class NewsForm(ModelForm):
    class Meta:
        model = News
        fields = ["title", "content", "pinned_thumbnail"]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'pinned_thumbnail': forms.URLInput(attrs={'class': 'form-control'}),
        }

class ImageNewsForm(ModelForm):
    class Meta:
        model = ImageNews
        fields = ['image_url']
        widgets = {
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan URL gambar tambahan...'}),
        }

# Membuat FormSet yang menghubungkan News dengan ImageNews
# 'extra=1' berarti formset akan menampilkan 1 form kosong tambahan secara default.
# 'can_delete=True' memungkinkan pengguna untuk menghapus gambar yang sudah ada.
ImageNewsFormSet = inlineformset_factory(
    News, 
    ImageNews, 
    form=ImageNewsForm, 
    extra=0, 
    can_delete=True
)