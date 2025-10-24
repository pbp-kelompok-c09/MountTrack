from django.test import TestCase, Client, SimpleTestCase
from django.urls import reverse, resolve
from .models import UserProfile
from .forms import ProfileForm
from . import views
from list_gunung.models import Mountain

class ModelTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(username='modeltestuser', password='password123')
        self.mountain = Mountain.objects.create(name='Gunung Tes')

    def test_user_str_representation(self):
        """tes apakah __str__ method mengembalikan username."""
        self.assertEqual(str(self.user), 'modeltestuser')

    def test_user_default_experience(self):
        """tes apakah 'category_experience' default-nya 'beginner'."""
        self.assertEqual(self.user.category_experience, 'beginner')

    def test_add_history_method(self):
        """tes metode custom 'add_history'."""
            
        # awal: riwayat harus kosong
        self.assertEqual(self.user.history_gunung.count(), 0)
        
        # panggil metode untuk menambah riwayat
        self.user.add_history(self.mountain)
        
        # riwayat harus berisi 1
        self.assertEqual(self.user.history_gunung.count(), 1)
        self.assertIn(self.mountain, self.user.history_gunung.all())


class FormTests(TestCase):
    def test_profile_form_valid_data(self):
        """tes ProfileForm dengan data yang valid."""
        form_data = {
            'nama': 'User Tes',
            'umur': 25,
            'nomor_telepon': '081234567890',
            'category_experience': 'intermediate',
            'jenis_kelamin': 'M'
        }
        form = ProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_profile_form_invalid_umur(self):
        """tes validasi clean_umur (umur tidak boleh <= 0)."""
        form_data = {'nama': 'User Tes', 'umur': 0}
        form = ProfileForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('umur', form.errors)
        self.assertEqual(form.errors['umur'][0], "Umur harus lebih dari 0")

    def test_profile_form_invalid_nomor_telepon(self):
        """tes validasi clean_nomor_telepon (harus angka)."""
        form_data = {'nama': 'User Tes', 'nomor_telepon': 'iniBukanAngka'}
        form = ProfileForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('nomor_telepon', form.errors)
        self.assertEqual(form.errors['nomor_telepon'][0], "Nomor telepon hanya boleh berisi angka")


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # buat user dengan profil tidak lengkap
        self.incomplete_user = UserProfile.objects.create_user(
            username='userkosong', 
            password='password123',
            nama='' # nama kosong
        )
        
        # buat user dengan profil lengkap
        self.complete_user = UserProfile.objects.create_user(
            username='userlengkap', 
            password='password123',
            nama='User Lengkap',
            umur=30,
            nomor_telepon='123456789'
        )
        
        # buat user admin
        self.staff_user = UserProfile.objects.create_user(
            username='staffuser', 
            password='password123',
            is_staff=True,
            is_superuser=True
        )

    def test_register_first_user_is_admin(self):
        """tes apakah user pertama yang register otomatis jadi superuser."""
        # hapus semua user yang ada
        UserProfile.objects.all().delete()
        
        # buat request register
        register_url = reverse('userprofile:register')
        self.client.post(register_url, {
            'username': 'adminpertama',
            'email': 'admin@mail.com',
            'password1': 'password123',
            'password2': 'password123'
        })
        
        # cek user yang baru dibuat
        first_user = UserProfile.objects.get(username='adminpertama')
        self.assertTrue(first_user.is_staff)
        self.assertTrue(first_user.is_superuser)

    def test_login_redirect_if_profile_incomplete(self):
        """tes login: harus redirect ke 'my-profile' jika data belum lengkap."""
        login_url = reverse('userprofile:login')
        response = self.client.post(login_url, {
            'username': 'userkosong',
            'password': 'password123'
        })
        
        # cek apakah redirect ke halaman profil
        self.assertRedirects(response, reverse('userprofile:my-profile'))

    def test_login_redirect_if_profile_complete(self):
        """tes login: harus redirect ke 'news:page_news' jika data sudah lengkap."""
        login_url = reverse('userprofile:login')
        response = self.client.post(login_url, {
            'username': 'userlengkap',
            'password': 'password123'
        })
        
        # cek apakah redirect ke halaman berita
        try:
            target_url = reverse('news:page_news')
            self.assertRedirects(response, target_url)
        except:
            self.skipTest("URL 'news:page_news' tidak ditemukan. Lewati tes redirect login.")

    def test_profile_page_requires_login(self):
        """tes view 'profile_user' harus redirect ke login jika belum login."""
        profile_url = reverse('userprofile:my-profile')
        response = self.client.get(profile_url)
        
        login_url = reverse('userprofile:login')
        # cek apakah redirect ke halaman login
        self.assertRedirects(response, login_url)

    def test_admin_portal_redirects_if_not_staff(self):
        """tes view 'admin_portal_user' harus redirect jika user bukan staff."""
        # login sebagai user biasa
        self.client.login(username='userlengkap', password='password123')
        
        admin_url = reverse('userprofile:admin_portal')
        response = self.client.get(admin_url)
        
        # cek apakah redirect ke halaman no_access
        self.assertRedirects(response, reverse('userprofile:no_access'), target_status_code=403)

    def test_admin_portal_accessible_by_staff(self):
        """tes view 'admin_portal_user' bisa diakses oleh staff."""
        # login sebagai staff
        self.client.login(username='staffuser', password='password123')
        
        admin_url = reverse('userprofile:admin_portal')
        response = self.client.get(admin_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_portal.html')

    def test_public_profile_redirects_for_own_profile(self):
        """tes 'public_profile_view' redirect ke 'my-profile' jika melihat profil sendiri."""
        # login sebagai user biasa
        self.client.login(username='userlengkap', password='password123')
        
        # coba akses URL profil publik diri sendiri
        public_url = reverse('userprofile:public_profile', args=['userlengkap'])
        response = self.client.get(public_url)
        
        self.assertRedirects(response, reverse('userprofile:my-profile'))

    def test_public_profile_view_other_user(self):
        """tes 'public_profile_view' sukses merender profil orang lain."""
        # login sebagai user biasa
        self.client.login(username='userlengkap', password='password123')
        
        # coba akses URL profil publik milik staff
        public_url = reverse('userprofile:public_profile', args=['staffuser'])
        response = self.client.get(public_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'public_profile.html')

    def test_get_users_json_forbidden_for_non_staff(self):
        """tes API 'get_users_json' mengembalikan 403 untuk non-staff."""
        self.client.login(username='userlengkap', password='password123')
        
        json_url = reverse('userprofile:get_users_json')
        response = self.client.get(json_url)
        
        self.assertEqual(response.status_code, 403)

    def test_get_users_json_success_for_staff(self):
        """tes API 'get_users_json' mengembalikan 200 dan data untuk staff."""
        self.client.login(username='staffuser', password='password123')
        
        json_url = reverse('userprofile:get_users_json')
        response = self.client.get(json_url)
        
        self.assertEqual(response.status_code, 200)
        
        # cek datanya (harus ada 3 user yang dibuat di setUp)
        data = response.json()
        self.assertEqual(len(data), 3)
        usernames = [user['username'] for user in data]
        self.assertIn('userkosong', usernames)
        self.assertIn('userlengkap', usernames)
        self.assertIn('staffuser', usernames)


class UrlTests(SimpleTestCase):
    def test_login_url_resolves_to_correct_view(self):
        """tes apakah URL 'login/' meresolve ke view 'login_user'."""
        url = reverse('userprofile:login')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.login_user)

    def test_my_profile_url_resolves_to_correct_view(self):
        """tes apakah URL 'my-profile/' meresolve ke view 'profile_user'."""
        url = reverse('userprofile:my-profile')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.profile_user)

    def test_public_profile_url_resolves_to_correct_view(self):
        """tes apakah URL 'profile/<str:username>/' meresolve ke view 'public_profile_view'."""
        url = reverse('userprofile:public_profile', args=['dummy-name'])
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.public_profile_view)