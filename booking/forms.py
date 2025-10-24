from django import forms

class BookingForm(forms.Form):
    pax = forms.IntegerField(label='Jumlah Anggota', min_value=1, initial=1)
    porter_hire = forms.ChoiceField(
        choices=[('', '---'), ('yes','Ya'),('no','Tidak')],
        required=False,
        label='Sewa Porter? (jika diperlukan)'
    )

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
