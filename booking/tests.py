from django.test import TestCase, Client
from django.urls import reverse
from .models import Booking, UserProfile
from list_gunung.models import Mountain

class ModelTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(username='testuser', password='password123')
        self.mountain = Mountain.objects.create(name='Gunung Test', location='Indonesia')
        self.booking = Booking.objects.create(
            user=self.user,
            gunung=self.mountain,
            pax=3,
            porter_required=True
        )

    def test_booking_str_representation(self):
        self.assertEqual(str(self.booking), f"Booking #{self.booking.id} - {self.user.username} -> Gunung Test")

    def test_booking_creation(self):
        self.assertEqual(self.booking.user.username, 'testuser')
        self.assertEqual(self.booking.gunung.name, 'Gunung Test')
        self.assertEqual(self.booking.pax, 3)
        self.assertTrue(self.booking.porter_required)


class FormTests(TestCase):
    def test_booking_form_valid_data(self):
        form_data = {
            'pax': 3,
            'porter_hire': 'yes'
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_booking_form_invalid_pax(self):
        form_data = {'pax': 0}
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('pax', form.errors)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserProfile.objects.create_user(username='testuser', password='password123')
        self.mountain = Mountain.objects.create(name='Gunung Test', location='Indonesia')

    def test_booking_view(self):
        self.client.login(username='testuser', password='password123')
        url = reverse('booking:booking_view', args=[self.mountain.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_form.html')

    def test_booking_summary_view(self):
        self.client.login(username='testuser', password='password123')
        booking = Booking.objects.create(
            user=self.user,
            gunung=self.mountain,
            pax=3,
            porter_required=True
        )
        url = reverse('booking:booking_summary', args=[booking.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_summary.html')

    def test_all_bookings_view(self):
        self.client.login(username='testuser', password='password123')
        url = reverse('booking:all_bookings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/all_bookings.html')
