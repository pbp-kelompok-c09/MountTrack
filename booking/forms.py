from django import forms
from .models import Booking, BookingMember, Mountain
from django.forms import modelformset_factory

class BookingForm(forms.ModelForm):
    gunung = forms.ModelChoiceField(
        queryset=Mountain.objects.all(),
        empty_label="Pilih Gunung",
        required=True,  # Pastikan field ini wajib
    )

    pax = forms.IntegerField(
        label='Jumlah Anggota Tambahan',
        min_value=0,
        initial=0,
        required=True,  # Pastikan field ini wajib
    )

    porter_hire = forms.ChoiceField(
        choices=[('', '---'), ('yes','Ya'),('no','Tidak')],
        required=False,
        label='Sewa Porter? (jika diperlukan)'
    )

    class Meta:
        model = Booking
        fields = ['gunung', 'pax', 'porter_hire']

    def __init__(self, *args, **kwargs):
        pax = kwargs.pop('pax', None)
        super().__init__(*args, **kwargs)
        # Only create fields for additional members (pax = additional members, not including user)
        for i in range(pax or 0):
            self.fields[f'anggota_{i}_name'] = forms.CharField(
                label=f'Nama Anggota Tambahan {i+1}', max_length=100, required=True
            )
            self.fields[f'anggota_{i}_age'] = forms.IntegerField(
                label=f'Usia Anggota Tambahan {i+1}', min_value=0, required=True
            )
            self.fields[f'anggota_{i}_gender'] = forms.ChoiceField(
                choices=[('M', 'Laki-laki'), ('F', 'Perempuan')],
                label=f'Jenis Kelamin Anggota Tambahan {i+1}',
                required=True
            )
            self.fields[f'anggota_{i}_level'] = forms.ChoiceField(
                choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
                label=f'Level Anggota Tambahan {i+1}',
                required=True
            )

