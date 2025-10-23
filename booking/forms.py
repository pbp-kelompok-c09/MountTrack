from django import forms

class BookingForm(forms.Form):
    pax = forms.IntegerField(label='Number of People', min_value=1)
    levels = forms.MultipleChoiceField(
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        widget=forms.CheckboxSelectMultiple,
        label='Levels (Choose at least one)'
    )
