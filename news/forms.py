from django import forms
from django.forms import ModelForm, inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from news.models import News, ImageNews
import requests



# FORM UTAMA UNTUK BERITA

class NewsForm(ModelForm):
    class Meta:
        model = News
        fields = ["title", "content", "pinned_thumbnail"]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masukkan judul berita...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Tulis isi berita di sini...'
            }),
            'pinned_thumbnail': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masukkan URL thumbnail utama (opsional)...'
            }),
        }

    def clean_pinned_thumbnail(self):
        url = self.cleaned_data.get('pinned_thumbnail')
        if url:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code >= 400:
                    raise ValidationError("URL gambar tidak dapat diakses (status code error).")
            except requests.RequestException:
                raise ValidationError("URL gambar tidak dapat diakses.")
        return url



# FORM UNTUK GAMBAR TAMBAHAN

class ImageNewsForm(ModelForm):
    class Meta:
        model = ImageNews
        fields = ['image_url']
        widgets = {
            'image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masukkan URL gambar tambahan...'
            }),
        }

    def clean_image_url(self):
        url = self.cleaned_data.get('image_url')
        if url:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code >= 400:
                    raise ValidationError("URL gambar tambahan tidak dapat diakses (status code error).")
            except requests.RequestException:
                raise ValidationError("URL gambar tambahan tidak dapat diakses.")
        return url



# BASE FORMSET UNTUK VALIDASI FORMSET GAMBAR

class BaseImageNewsFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            # Skip form kosong atau yang ditandai untuk dihapus
            if not form.cleaned_data or form.cleaned_data.get('DELETE', False):
                continue
            image_url = form.cleaned_data.get('image_url')
            if not image_url:
                raise ValidationError("Semua gambar yang diisi harus memiliki URL valid.")


# IN-LINE FORMSET

ImageNewsFormSet = inlineformset_factory(
    News,
    ImageNews,
    form=ImageNewsForm,
    formset=BaseImageNewsFormSet,
    extra=0,
    can_delete=True,
    validate_min=True,
    min_num=0
)
