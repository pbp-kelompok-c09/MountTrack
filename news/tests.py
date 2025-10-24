import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from .models import News, ImageNews

User = get_user_model()

class NewsViewsTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.password = 'testpassword123'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=self.password
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password=self.password,
            is_staff=True
        )

        self.news1 = News.objects.create(
            title="Berita Pertama",
            content="Isi berita pertama.",
            user=self.staff_user,
            pinned_thumbnail=""
        )
        self.news2 = News.objects.create(
            title="Berita Kedua",
            content="Isi berita kedua.",
            user=self.staff_user,
            pinned_thumbnail=""
        )
        self.image1 = ImageNews.objects.create(
            news=self.news1,
            image_url="https://example.com/image1.jpg"
        )

        self.main_url = reverse('news:page_news')
        self.create_url = reverse('news:create_news')
        self.search_url = reverse('news:search_news')
        self.show_url = reverse('news:show_news', args=[self.news1.id])
        self.edit_url = reverse('news:edit_news', args=[self.news1.id])
        self.delete_url = reverse('news:delete_news', args=[self.news1.id])
        try:
            self.login_url = reverse('userprofile:login')
        except Exception:
            self.login_url = '/accounts/login/'

    # ---- show_main ----
    def test_show_main_view_loads_correctly(self):
        response = self.client.get(self.main_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'page_news.html')
        self.assertContains(response, self.news1.title)
        self.assertContains(response, self.news2.title)

    # ---- show_news ----
    def test_show_news_view_loads_correctly(self):
        initial_views = self.news1.news_views
        response = self.client.get(self.show_url)
        self.news1.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_news.html')
        self.assertContains(response, self.news1.title)
        self.assertContains(response, self.image1.image_url)
        self.assertEqual(self.news1.news_views, initial_views + 1)

    def test_show_news_view_404_for_invalid_id(self):
        invalid_url = reverse('news:show_news', args=[uuid.uuid4()])
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    # ---- create_news ----
    def test_create_news_view_redirects_if_not_logged_in(self):
        response = self.client.get(self.create_url)
        expected_redirect = f'{self.login_url}?next={self.create_url}'
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)

    def test_create_news_view_loads_for_logged_in_user(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_news.html')
        self.assertIn('news_form', response.context)
        self.assertIn('image_formset', response.context)

    def test_create_news_view_fails_if_invalid_form(self):
        self.client.login(username=self.user.username, password=self.password)
        invalid_data = {
            'title': '',
            'content': 'Isi berita',
            'pinned_thumbnail': '',
            'TOTAL_FORMS': '0',
            'INITIAL_FORMS': '0',
            'MIN_NUM_FORMS': '0',
            'MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(self.create_url, invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_news.html')
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("kesalahan pada form" in m for m in messages))

    


    # ---- delete_news ----
    def test_delete_news_requires_post(self):
        self.client.login(username=self.staff_user.username, password=self.password)
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 405)

    def test_delete_news_requires_staff(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(self.delete_url)
        expected_redirect = f'{self.login_url}?next={self.delete_url}'
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)

    def test_delete_news_successful(self):
        self.client.login(username=self.staff_user.username, password=self.password)
        self.assertTrue(News.objects.filter(id=self.news1.id).exists())
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, self.main_url)
        self.assertFalse(News.objects.filter(id=self.news1.id).exists())
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("dihapus" in m for m in messages))

    # ---- edit_news ----
    def test_edit_news_requires_staff(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.edit_url)
        expected_redirect = f'{self.login_url}?next={self.edit_url}'
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)

    @patch('news.forms.requests.head')
    def test_edit_news_loads_for_staff(self, mock_head):
        mock_head.return_value = MagicMock(status_code=200)
        self.client.login(username=self.staff_user.username, password=self.password)
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_news.html')
        self.assertContains(response, self.news1.title)

    @patch('news.forms.requests.head')
    def test_edit_news_post_success(self, mock_head):
        mock_head.return_value = MagicMock(status_code=200)
        self.client.login(username=self.staff_user.username, password=self.password)
        data = {
            'title': 'Berita Pertama Diedit',
            'content': 'Isi diperbarui',
            'pinned_thumbnail': '',
            'images-TOTAL_FORMS': '1',
            'images-INITIAL_FORMS': '1',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '1000',
            'images-0-id': str(self.image1.id),
            'images-0-image_url': self.image1.image_url,
            'images-0-DELETE': 'on',
        }
        response = self.client.post(self.edit_url, data)
        self.assertRedirects(response, self.main_url)

        self.news1.refresh_from_db()
        self.assertEqual(self.news1.title, 'Berita Pertama Diedit')
        self.assertFalse(ImageNews.objects.filter(id=self.image1.id).exists())

    # ---- search_news ----
    def test_search_news_returns_results(self):
        url = f"{self.search_url}?q=Pertama"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'news_list_partial.html')
        self.assertContains(response, self.news1.title)
        self.assertNotContains(response, self.news2.title)

    def test_search_news_returns_all_if_empty(self):
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'news_list_partial.html')
        self.assertContains(response, self.news1.title)
        self.assertContains(response, self.news2.title)
