from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class AccessControlTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@x.co', 'motdepasse123')
        self.normal = User.objects.create_user('jo', password='motdepasse123')

    def test_anonymous_redirected(self):
        r = self.client.get(reverse('bo_overview'))
        self.assertEqual(r.status_code, 302)        # vers la connexion

    def test_normal_user_gets_404(self):
        self.client.force_login(self.normal)
        r = self.client.get(reverse('bo_overview'))
        self.assertEqual(r.status_code, 404)        # on ne révèle pas l'existence

    def test_superuser_ok(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('bo_overview'))
        self.assertEqual(r.status_code, 200)
