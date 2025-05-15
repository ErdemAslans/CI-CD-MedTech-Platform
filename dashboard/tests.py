from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.doctor = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='testpassword123',
            user_type='doctor'
        )
        self.admin = User.objects.create_user(
            username='testadmin',
            email='admin@example.com',
            password='testpassword123',
            user_type='admin',
            is_staff=True
        )
        
        # API endpoint'leri
        self.stats_url = reverse('dashboard-stats')
        self.case_summary_url = reverse('case-summary')
        self.prediction_distribution_url = reverse('prediction-distribution')
    
    def test_stats_endpoint_auth(self):
        """İzinsiz kullanıcılar istatistiklere erişememeli"""
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_doctor_can_access_stats(self):
        """Doktorlar kendi istatistiklerine erişebilmeli"""
        self.client.force_authenticate(user=self.doctor)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_can_access_doctor_activity(self):
        """Adminler doktor aktivite istatistiklerine erişebilmeli"""
        self.client.force_authenticate(user=self.admin)
        doctor_activity_url = reverse('doctor-activity')
        response = self.client.get(doctor_activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_doctor_cannot_access_doctor_activity(self):
        """Doktorlar doktor aktivite istatistiklerine erişememeli"""
        self.client.force_authenticate(user=self.doctor)
        doctor_activity_url = reverse('doctor-activity')
        response = self.client.get(doctor_activity_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)