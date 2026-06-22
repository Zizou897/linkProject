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


class KpiTests(TestCase):
    def test_funnel_and_counts(self):
        from backoffice.kpis import overview_context
        from app.models import VozaviForm, VozaviResponse
        u1 = User.objects.create_user('a', password='x12345678')
        u2 = User.objects.create_user('b', password='x12345678')
        User.objects.create_user('c', password='x12345678')        # inscrit, sans formulaire
        User.objects.create_superuser('boss', 'b@x.co', 'x12345678')  # exclu des stats
        f1 = VozaviForm.objects.create(user=u1, title='F1', slug='s1', status='active')
        VozaviForm.objects.create(user=u2, title='F2', status='draft')  # créé, non publié
        VozaviResponse.objects.create(form=f1)

        ctx = overview_context()
        self.assertEqual(ctx['users_total'], 3)        # superadmin exclu
        self.assertEqual(ctx['funnel']['signed_up'], 3)
        self.assertEqual(ctx['funnel']['created'], 2)  # u1, u2
        self.assertEqual(ctx['funnel']['published'], 1)  # u1
        self.assertEqual(ctx['funnel']['with_response'], 1)  # u1
        self.assertEqual(ctx['forms_total'], 2)
        self.assertEqual(ctx['responses_total'], 1)
        self.assertEqual(len(ctx['signups_series']), 30)


class ChromeRenderTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'motdepasse123')
        self.client.force_login(self.admin)

    def test_all_nav_pages_render(self):
        for name in ['bo_overview', 'bo_users', 'bo_journal', 'bo_health']:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, name)
            self.assertContains(r, 'bo-side')          # chrome present


class OverviewRenderTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'x12345678')
        self.client.force_login(self.admin)

    def test_overview_shows_kpis(self):
        from app.models import VozaviForm
        User.objects.create_user('a', password='x12345678')
        VozaviForm.objects.create(title='F', status='active', slug='s1')
        r = self.client.get(reverse('bo_overview'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Utilisateurs')
        self.assertContains(r, 'Funnel')

    def test_kpis_partial_ok(self):
        r = self.client.get(reverse('bo_kpis_partial'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'bo-card')
