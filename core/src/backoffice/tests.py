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


class UsersListTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'x12345678')
        self.client.force_login(self.admin)

    def test_list_shows_users_and_search(self):
        from app.models import VozaviForm
        u = User.objects.create_user('awa', email='awa@x.co', password='x12345678')
        VozaviForm.objects.create(user=u, title='F', status='active', slug='s1')
        r = self.client.get(reverse('bo_users'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'awa@x.co')
        r2 = self.client.get(reverse('bo_users'), {'q': 'introuvable'})
        self.assertNotContains(r2, 'awa@x.co')


class UserActionsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'x12345678')
        self.admin2 = User.objects.create_superuser('boss2', 'b2@x.co', 'x12345678')
        self.target = User.objects.create_user('cible', password='x12345678')
        self.client.force_login(self.admin)

    def test_detail_renders(self):
        r = self.client.get(reverse('bo_user_detail', args=[self.target.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'cible')

    def test_deactivate_sets_inactive_and_logs(self):
        from app.models import ActivityEvent
        self.client.post(reverse('bo_user_toggle', args=[self.target.pk]))
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        self.assertTrue(ActivityEvent.objects.filter(event_type='account_deactivated').exists())

    def test_cannot_deactivate_self(self):
        self.client.post(reverse('bo_user_toggle', args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)        # inchangé

    def test_cannot_deactivate_other_superuser(self):
        self.client.post(reverse('bo_user_toggle', args=[self.admin2.pk]))
        self.admin2.refresh_from_db()
        self.assertTrue(self.admin2.is_active)

    def test_delete_removes_user_and_logs(self):
        from app.models import ActivityEvent
        pk = self.target.pk
        self.client.post(reverse('bo_user_delete', args=[pk]))
        self.assertFalse(User.objects.filter(pk=pk).exists())
        self.assertTrue(ActivityEvent.objects.filter(event_type='account_deleted_by_admin').exists())

    def test_cannot_delete_other_superuser(self):
        self.client.post(reverse('bo_user_delete', args=[self.admin2.pk]))
        self.assertTrue(User.objects.filter(pk=self.admin2.pk).exists())

    def test_reactivate_logs_account_reactivated(self):
        from app.models import ActivityEvent
        self.target.is_active = False
        self.target.save(update_fields=['is_active'])
        self.client.post(reverse('bo_user_toggle', args=[self.target.pk]))
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.assertTrue(ActivityEvent.objects.filter(event_type='account_reactivated').exists())
        self.assertFalse(ActivityEvent.objects.filter(event_type='user_login', label=self.target.get_username()).exists())


class JournalTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'x12345678')
        self.client.force_login(self.admin)

    def test_journal_lists_and_filters(self):
        from app.models import ActivityEvent
        ActivityEvent.objects.create(event_type='form_published', label='Resto')
        ActivityEvent.objects.create(event_type='response_received', label='NPS')
        r = self.client.get(reverse('bo_journal'))
        self.assertContains(r, 'Resto')
        self.assertContains(r, 'NPS')
        r2 = self.client.get(reverse('bo_journal'), {'type': 'form_published'})
        self.assertContains(r2, 'Resto')
        self.assertNotContains(r2, 'NPS')

    def test_feed_partial_ok(self):
        r = self.client.get(reverse('bo_journal_feed'))
        self.assertEqual(r.status_code, 200)


class HealthTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'x12345678')
        self.client.force_login(self.admin)

    def test_health_counts(self):
        from app.models import ActivityEvent, ContactMessage
        ActivityEvent.objects.create(event_type='email_failed', success=False, label='x')
        ContactMessage.objects.create(name='A', email='a@x.co', message='hi')
        r = self.client.get(reverse('bo_health'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Contacts non lus')
        self.assertContains(r, 'E-mails échoués')
