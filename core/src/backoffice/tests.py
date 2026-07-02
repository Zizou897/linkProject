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
        for name in ['bo_overview', 'bo_users', 'bo_journal', 'bo_contacts',
                     'bo_health', 'bo_search']:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, name)
            self.assertContains(r, 'adm-rail')         # chrome present


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
        self.assertContains(r, 'adm-metric')


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


class AdminAuthTests(TestCase):
    """Connexion / déconnexion dédiées au back-office (super-admin)."""

    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'motdepasse123')
        self.normal = User.objects.create_user('jo', email='jo@x.co', password='motdepasse123')

    def test_anonymous_redirected_to_admin_login(self):
        r = self.client.get(reverse('bo_overview'))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.startswith(reverse('bo_login')))   # pas la connexion client
        self.assertIn('next=', r.url)

    def test_login_page_renders(self):
        r = self.client.get(reverse('bo_login'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Espace admin')

    def test_superuser_login_succeeds(self):
        r = self.client.post(reverse('bo_login'),
                             {'username': 'boss', 'password': 'motdepasse123'})
        self.assertRedirects(r, reverse('bo_overview'), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse('bo_overview')).status_code, 200)

    def test_normal_user_cannot_login_admin(self):
        r = self.client.post(reverse('bo_login'),
                             {'username': 'jo', 'password': 'motdepasse123'})
        self.assertEqual(r.status_code, 200)              # réaffichage avec erreur
        self.assertContains(r, 'accès non autorisé')
        # non connecté → l'accès admin redirige toujours vers le login
        self.assertEqual(self.client.get(reverse('bo_overview')).status_code, 302)

    def test_login_honors_safe_next(self):
        r = self.client.post(reverse('bo_login'),
                             {'username': 'boss', 'password': 'motdepasse123',
                              'next': reverse('bo_journal')})
        self.assertRedirects(r, reverse('bo_journal'), fetch_redirect_response=False)

    def test_login_rejects_unsafe_next(self):
        r = self.client.post(reverse('bo_login'),
                             {'username': 'boss', 'password': 'motdepasse123',
                              'next': 'http://evil.example/x'})
        self.assertRedirects(r, reverse('bo_overview'), fetch_redirect_response=False)

    def test_logout(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('bo_logout'))
        self.assertRedirects(r, reverse('bo_login'), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse('bo_overview')).status_code, 302)

    def test_sidebar_shows_logout(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('bo_overview'))
        self.assertContains(r, reverse('bo_logout'))
        self.assertContains(r, 'Déconnexion')


class ContactMessagesTests(TestCase):
    def setUp(self):
        from app.models import ContactMessage
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'motdepasse123')
        self.client.force_login(self.admin)
        self.m1 = ContactMessage.objects.create(
            name='Alice', email='alice@x.co', category='support', message='Bug sur le builder')
        self.m2 = ContactMessage.objects.create(
            name='Bob', email='bob@x.co', category='billing', message='Question de facturation',
            is_read=True)

    def test_list_shows_messages(self):
        r = self.client.get(reverse('bo_contacts'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Alice')
        self.assertContains(r, 'Bug sur le builder')
        self.assertContains(r, 'Bob')

    def test_filter_unread(self):
        r = self.client.get(reverse('bo_contacts'), {'status': 'unread'})
        self.assertContains(r, 'Alice')
        self.assertNotContains(r, 'Bob')

    def test_filter_category_and_search(self):
        r = self.client.get(reverse('bo_contacts'), {'cat': 'billing'})
        self.assertContains(r, 'Bob')
        self.assertNotContains(r, 'Alice')
        r = self.client.get(reverse('bo_contacts'), {'q': 'builder'})
        self.assertContains(r, 'Alice')
        self.assertNotContains(r, 'Bob')

    def test_toggle_read(self):
        r = self.client.post(reverse('bo_contact_toggle', args=[self.m1.pk]))
        self.assertRedirects(r, reverse('bo_contacts'), fetch_redirect_response=False)
        self.m1.refresh_from_db()
        self.assertTrue(self.m1.is_read)

    def test_toggle_honors_safe_next(self):
        next_url = reverse('bo_contacts') + '?status=unread'
        r = self.client.post(reverse('bo_contact_toggle', args=[self.m1.pk]), {'next': next_url})
        self.assertRedirects(r, next_url, fetch_redirect_response=False)

    def test_toggle_rejects_unsafe_next(self):
        r = self.client.post(reverse('bo_contact_toggle', args=[self.m1.pk]),
                             {'next': 'http://evil.example/x'})
        self.assertRedirects(r, reverse('bo_contacts'), fetch_redirect_response=False)

    def test_delete(self):
        from app.models import ContactMessage
        r = self.client.post(reverse('bo_contact_delete', args=[self.m2.pk]))
        self.assertRedirects(r, reverse('bo_contacts'), fetch_redirect_response=False)
        self.assertFalse(ContactMessage.objects.filter(pk=self.m2.pk).exists())

    def test_get_not_allowed_on_actions(self):
        self.assertEqual(self.client.get(reverse('bo_contact_toggle', args=[self.m1.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse('bo_contact_delete', args=[self.m1.pk])).status_code, 405)

    def test_requires_superuser(self):
        self.client.force_login(User.objects.create_user('jo', password='motdepasse123'))
        self.assertEqual(self.client.get(reverse('bo_contacts')).status_code, 404)

    def test_toggle_shows_toast(self):
        r = self.client.post(reverse('bo_contact_toggle', args=[self.m1.pk]), follow=True)
        self.assertContains(r, 'marqué comme lu')

    def test_unread_badge_in_rail(self):
        r = self.client.get(reverse('bo_overview'))
        self.assertContains(r, 'adm-count')   # 1 message non lu → badge visible


class GlobalSearchTests(TestCase):
    def setUp(self):
        from app.models import ContactMessage, VozaviForm
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'motdepasse123')
        self.client.force_login(self.admin)
        self.u = User.objects.create_user('marie', email='marie@x.co', password='x12345678')
        VozaviForm.objects.create(user=self.u, title='Enquête satisfaction', status='active', slug='enq')
        ContactMessage.objects.create(name='Paul', email='paul@x.co', message='Souci de connexion')

    def test_empty_query_renders(self):
        r = self.client.get(reverse('bo_search'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Recherche globale')

    def test_finds_across_models(self):
        r = self.client.get(reverse('bo_search'), {'q': 'marie'})
        self.assertContains(r, 'marie@x.co')
        r = self.client.get(reverse('bo_search'), {'q': 'satisfaction'})
        self.assertContains(r, 'Enquête satisfaction')
        r = self.client.get(reverse('bo_search'), {'q': 'connexion'})
        self.assertContains(r, 'Paul')

    def test_no_results(self):
        r = self.client.get(reverse('bo_search'), {'q': 'zzzzzz'})
        self.assertContains(r, 'Aucun résultat')

    def test_requires_superuser(self):
        self.client.force_login(User.objects.create_user('jo', password='motdepasse123'))
        self.assertEqual(self.client.get(reverse('bo_search')).status_code, 404)


class UsersFilterTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'b@x.co', 'motdepasse123')
        self.client.force_login(self.admin)
        User.objects.create_user('actif', email='actif@x.co', password='x12345678')
        inactive = User.objects.create_user('parti', email='parti@x.co', password='x12345678')
        inactive.is_active = False
        inactive.save(update_fields=['is_active'])

    def test_state_filter(self):
        r = self.client.get(reverse('bo_users'), {'state': 'active'})
        self.assertContains(r, 'actif@x.co')
        self.assertNotContains(r, 'parti@x.co')
        r = self.client.get(reverse('bo_users'), {'state': 'inactive'})
        self.assertContains(r, 'parti@x.co')
        self.assertNotContains(r, 'actif@x.co')
