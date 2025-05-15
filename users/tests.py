from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class UserTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'password2': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'doctor',
            'organization': 'Test Hospital'
        }
        self.login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
   
    def test_user_registration(self):
        """Kullanıcı kaydının test edilmesi"""
        url = reverse('users:register')
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, 302)  # 302 = Redirect after successful post
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')
   
    def test_user_login(self):
        """Kullanıcı girişinin test edilmesi"""
        # Önce kullanıcıyı oluştur
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
       
        url = reverse('users:login')
        response = self.client.post(url, self.login_data)
        self.assertEqual(response.status_code, 302)  # 302 = Redirect to success page
        self.assertRedirects(response, reverse('core:home'))  # Anasayfaya yönlendiriyor mu?
   
    def test_user_profile(self):
        """Kullanıcı profili erişiminin test edilmesi"""
        # Önce kullanıcıyı oluştur
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
       
        # Giriş yap
        self.client.login(username='test@example.com', password='testpassword123')
        
        # Profil sayfasına eriş
        profile_url = reverse('users:profile')
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')  # Kullanıcı adı sayfada var mı?