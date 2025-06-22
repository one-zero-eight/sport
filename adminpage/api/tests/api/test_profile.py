from django.contrib.auth.models import User
from rest_framework.test import APITestCase

class ProfileAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='dima', password='test123')
        self.client.login(username='dima', password='test123')

    def test_get_profile(self):
        response = self.client.get(f'/api/profile/{self.user.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'dima')
        self.assertIn('email', response.data)