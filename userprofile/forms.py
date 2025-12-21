from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class RegisterForm(UserCreationForm):
    class Meta:
        model = UserProfile
        fields = [
            'username',
            'nama',
            'umur',
            'nomor_telepon',
            'email',
            'category_experience',
            'jenis_kelamin',
            'password1',
            'password2',
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        required_fields = [
            'nama', 'umur', 'nomor_telepon', 'email',
            'category_experience', 'jenis_kelamin'
        ]
        for f in required_fields:
            self.fields[f].required = True

    def clean_umur(self):
        umur = self.cleaned_data.get('umur')
        if umur is not None and umur <= 0:
            raise forms.ValidationError("Umur harus lebih dari 0")
        return umur

    def clean_nomor_telepon(self):
        nomor = self.cleaned_data.get('nomor_telepon')
        if nomor and not nomor.isdigit():
            raise forms.ValidationError("Nomor telepon hanya boleh berisi angka")
        return nomor

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nama', 'umur', 'nomor_telepon', 'email', 'category_experience', 'jenis_kelamin']
        labels = {
            'nama': 'Nama Lengkap',
            'umur': 'Umur',
            'nomor_telepon': 'Nomor Telepon',
            'email' : 'Email',
            'category_experience': 'Kategori Pengalaman',
            'jenis_kelamin': 'Jenis Kelamin',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ubah teks yang tampil di dropdown my profile
        self.fields['jenis_kelamin'].choices = [
            ('M', 'Laki-laki'),
            ('F', 'Perempuan'),
            ('O', 'Lainnya'),
        ]
        self.fields['category_experience'].choices = [
            ('beginner', 'Pemula (Beginner)'),
            ('intermediate', 'Menengah (Intermediate)'),
            ('advanced', 'Berpengalaman (Advanced)'),
        ]

    def clean_umur(self):
        umur = self.cleaned_data.get('umur')
        if umur is not None and umur <= 0:
            raise forms.ValidationError("Umur harus lebih dari 0")
        return umur

    def clean_nomor_telepon(self):
        nomor = self.cleaned_data.get('nomor_telepon')
        if nomor and not nomor.isdigit():
            raise forms.ValidationError("Nomor telepon hanya boleh berisi angka")
        return nomor
