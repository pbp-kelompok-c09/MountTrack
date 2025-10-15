from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class RegisterForm(UserCreationForm):
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nama', 'umur', 'nomor_telepon', 'category_experience', 'jenis_kelamin']

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
