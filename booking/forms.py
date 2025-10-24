from django import forms
from .models import BookingMember

class BookingForm(forms.Form):
    """
    Form dinamis yang membuat field anggota_0_name ... anggota_N_level berdasarkan argumen pax.
    Dipakai oleh booking.views.booking_view.
    """
    porter_hire = forms.ChoiceField(
        choices=[('no', 'Tidak'), ('yes', 'Ya')],
        required=False,
        widget=forms.RadioSelect
    )

    def __init__(self, *args, pax=1, **kwargs):
        super().__init__(*args, **kwargs)
        # simpan pax sebagai hidden field agar POST mengirimnya kembali
        self.fields['pax'] = forms.IntegerField(min_value=1, initial=pax, widget=forms.HiddenInput)

        # generate anggota fields sesuai pax
        for i in range(int(pax or 1)):
            self.fields[f'anggota_{i}_name'] = forms.CharField(
                max_length=150,
                label=f'Nama Anggota {i+1}',
            )
            self.fields[f'anggota_{i}_age'] = forms.IntegerField(
                required=False,
                min_value=0,
                label=f'Usia Anggota {i+1}',
            )
            self.fields[f'anggota_{i}_gender'] = forms.ChoiceField(
                choices=BookingMember.GENDER_CHOICES,
                required=False,
                label=f'Jenis Kelamin Anggota {i+1}',
            )
            self.fields[f'anggota_{i}_level'] = forms.ChoiceField(
                choices=BookingMember.LEVEL_CHOICES,
                label=f'Tingkat Anggota {i+1}',
            )

    def clean(self):
        cleaned = super().clean()
        # pastikan jumlah anggota sesuai pax
        pax = cleaned.get('pax') or 1
        for i in range(int(pax)):
            name = cleaned.get(f'anggota_{i}_name')
            level = cleaned.get(f'anggota_{i}_level')
            if not name:
                self.add_error(f'anggota_{i}_name', 'Nama anggota diperlukan.')
            if not level:
                self.add_error(f'anggota_{i}_level', 'Tingkat anggota diperlukan.')
        return cleaned