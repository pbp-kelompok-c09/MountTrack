from django.test import TestCase
from django.urls import reverse
from .models import Booking, BookingMember
from list_gunung.models import Mountain
from userprofile.models import UserProfile
from .forms import BookingForm
from django.test.client import Client
import json


class BookingTests(TestCase):
    def setUp(self):
        # Create test user and mountain
        self.user = UserProfile.objects.create_user(username='testuser', password='password123')
        self.mountain = Mountain.objects.create(name='Gunung Test', height_mdpl=1000)  # Assuming height_mdpl is a required field.

    # Model Tests
    def test_booking_str_representation(self):
        """Test the string representation of the booking"""
        booking = Booking.objects.create(
            user=self.user,
            gunung=self.mountain,
            pax=3,
            porter_required=True
        )
        self.assertEqual(str(booking), f"Booking #{booking.id} - {self.user.username} -> Gunung Test")

    def test_booking_creation(self):
        """Test booking creation and fields"""
        booking = Booking.objects.create(
            user=self.user,
            gunung=self.mountain,
            pax=3,
            porter_required=True
        )
        self.assertEqual(booking.user.username, 'testuser')
        self.assertEqual(booking.gunung.name, 'Gunung Test')
        self.assertEqual(booking.pax, 3)
        self.assertTrue(booking.porter_required)

    def test_booking_member_creation(self):
        """Test the creation of booking members"""
        booking = Booking.objects.create(
            user=self.user,
            gunung=self.mountain,
            pax=3,
            porter_required=True
        )
        member = BookingMember.objects.create(
            booking=booking,
            name="John Doe",
            age=25,
            gender='M',
            level='beginner'
        )
        self.assertEqual(member.name, "John Doe")
        self.assertEqual(member.booking, booking)
        self.assertEqual(member.age, 25)

    # Form Tests
    def test_booking_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'gunung': self.mountain.id,
            'pax': 3,
            'porter_hire': 'yes',
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_booking_form_invalid_pax(self):
        """Test form with invalid pax"""
        form_data = {
            'gunung': self.mountain.id,
            'pax': 0,  # Invalid pax
            'porter_hire': 'yes',
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('pax', form.errors)

    def test_booking_form_missing_field(self):
        """Test form submission without required fields"""
        form_data = {
            'gunung': self.mountain.id,
            'porter_hire': 'yes',
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('pax', form.errors)

    # View Tests
    def test_booking_view(self):
        """Test booking view"""
        self.client.login(username='testuser', password='password123')
        url = reverse('booking:booking_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_form.html')

    def test_booking_summary_view(self):
        """Test booking summary after booking"""
        self.client.login(username='testuser', password='password123')
        booking = Booking.objects.create(
            user=self.user,
            gunung=self.mountain,
            pax=3,
            porter_required=True
        )
        url = reverse('booking:booking_summary', kwargs={'booking_id': booking.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_summary.html')

    def test_all_bookings_view(self):
        """Test all bookings view"""
        self.client.login(username='testuser', password='password123')
        url = reverse('booking:all_bookings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/all_bookings.html')

    # AJAX Tests
    def test_submit_booking(self):
        """Test successful AJAX booking submission"""
        self.client.login(username='testuser', password='password123')
        url = reverse('booking:submit')
        form_data = {
            'gunung': self.mountain.id,
            'pax': 3,
            'porter_hire': 'yes',
        }
        response = self.client.post(url, form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], 'Booking Successful')

    def test_submit_booking_invalid(self):
        """Test AJAX booking submission with invalid data"""
        self.client.login(username='testuser', password='password123')
        url = reverse('booking:submit')
        form_data = {
            'gunung': self.mountain.id,
            'pax': 0,  # Invalid pax
            'porter_hire': 'no',
        }
        response = self.client.post(url, form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('pax', response_data['errors'])

    def test_submit_booking_missing_field(self):
        """Test AJAX booking submission with missing data"""
        self.client.login(username='testuser', password='password123')
        url = reverse('booking:submit')
        form_data = {
            'gunung': self.mountain.id,
            'porter_hire': 'yes',
        }
        response = self.client.post(url, form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('pax', response_data['errors'])

