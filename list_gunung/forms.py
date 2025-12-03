from django import forms
from .models import Mountain

class MountainForm(forms.ModelForm):
    class Meta:
        model = Mountain
        fields = ['name', 'url', 'height_mdpl', 'province', 'image_url', 'description', 'availability', 'min_book', 'experience_required']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-green-600 focus:ring-2 focus:ring-green-200 transition duration-200',
                'placeholder': 'Nama Gunung'
            }),
            'url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-green-600 focus:ring-2 focus:ring-green-200 transition duration-200',
                'placeholder': 'URL Referensi'
            }),
            'height_mdpl': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-green-600 focus:ring-2 focus:ring-green-200 transition duration-200',
                'placeholder': 'Ketinggian (mdpl)',
                'min': '0'
            }),
            'province': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-green-600 focus:ring-2 focus:ring-green-200 transition duration-200',
                'placeholder': 'Provinsi'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-green-600 focus:ring-2 focus:ring-green-200 transition duration-200',
                'placeholder': 'URL Gambar (opsional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-green-600 focus:ring-2 focus:ring-green-200 transition duration-200',
                'placeholder': 'Deskripsi Gunung',
                'rows': 5
            }),
            'availability': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-green-600 rounded focus:ring-green-500 focus:ring-2'
            }),
            'min_book': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-green-600 focus:ring-2 focus:ring-green-200 transition duration-200',
                'placeholder': 'Jumlah minimum orang',
                'min': '1'
            }),
            'experience_required': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-green-600 focus:ring-2 focus:ring-green-200 transition duration-200'
            }),
        }
        labels = {
            'name': 'Nama Gunung',
            'url': 'URL Referensi',
            'height_mdpl': 'Ketinggian (mdpl)',
            'province': 'Provinsi',
            'image_url': 'URL Gambar',
            'description': 'Deskripsi',
            'availability': 'Tersedia untuk Booking',
            'min_book': 'Minimum Booking (orang)',
            'experience_required': 'Pengalaman yang Dibutuhkan',
        }

    def clean_height_mdpl(self):
        height = self.cleaned_data.get('height_mdpl')
        if height and height <= 0:
            raise forms.ValidationError('Ketinggian harus lebih dari 0 mdpl.')
        return height
