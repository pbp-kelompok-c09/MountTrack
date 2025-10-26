from django import forms
from .models import Booking, BookingMember, Mountain

class BookingForm(forms.ModelForm):
    gunung = forms.ModelChoiceField(
        queryset=Mountain.objects.all(),
        empty_label="Pilih Gunung",  # Pilihan default jika tidak ada yang dipilih
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    pax = forms.IntegerField(label='Jumlah Anggota', min_value=1, initial=1)
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
        for i in range(pax or 0):
            self.fields[f'anggota_{i}_name'] = forms.CharField(
                label=f'Nama Anggota {i+1}', max_length=100, required=True
            )
            self.fields[f'anggota_{i}_age'] = forms.IntegerField(
                label=f'Usia Anggota {i+1}', min_value=0, required=True
            )
            self.fields[f'anggota_{i}_gender'] = forms.ChoiceField(
                choices=[('M', 'Laki-laki'), ('F', 'Perempuan')],
                label=f'Jenis Kelamin Anggota {i+1}',
                required=True
            )
            self.fields[f'anggota_{i}_level'] = forms.ChoiceField(
                choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
                label=f'Level Anggota {i+1}',
                required=True
            )
