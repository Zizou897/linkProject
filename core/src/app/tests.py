"""
Base de tests Vozavi.

Couvre : création de formulaire, soumission de réponse (avec validation),
calcul des statistiques, génération des images Open Graph et pages publiques.

Lancement (DEBUG=True force SQLite pour la base de test) :
    DEBUG=True python manage.py test app
"""
import io

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse

from .models import VozaviForm, Question, VozaviResponse, Answer
from .views import _compute_question_stats

# Cache mémoire pour les tests : évite de dépendre de la table DatabaseCache.
LOCMEM_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


class FormCreationTests(TestCase):
    """new_form : création de formulaire et de ses questions."""

    def test_guest_creation_creates_form_questions_and_session(self):
        resp = self.client.post(reverse('new_form'), {'template_key': 'restaurant'})

        self.assertEqual(VozaviForm.objects.count(), 1)
        vform = VozaviForm.objects.get()
        self.assertEqual(vform.status, 'draft')
        self.assertIsNone(vform.user)                       # formulaire invité
        self.assertGreater(vform.questions.count(), 0)       # questions du modèle
        self.assertEqual(self.client.session.get('guest_form_pk'), vform.pk)
        self.assertRedirects(
            resp, reverse('edit_form', args=[vform.pk]),
            fetch_redirect_response=False,
        )

    def test_creation_assigns_user_when_authenticated(self):
        user = User.objects.create_user('createur', password='motdepasse123')
        self.client.force_login(user)

        self.client.post(reverse('new_form'), {'template_key': 'restaurant'})

        vform = VozaviForm.objects.get()
        self.assertEqual(vform.user, user)

    def test_unknown_template_falls_back_without_error(self):
        resp = self.client.post(reverse('new_form'), {'template_key': 'nexiste_pas'})
        self.assertEqual(VozaviForm.objects.count(), 1)
        self.assertEqual(resp.status_code, 302)


class AddQuestionFallbackTests(TestCase):
    """add_question : mode HTMX (fragment) et repli sans JS (redirection)."""

    def setUp(self):
        self.user = User.objects.create_user('createur', password='motdepasse123')
        self.client.force_login(self.user)
        self.vform = VozaviForm.objects.create(user=self.user, title='F', status='draft')

    def test_htmx_request_returns_partial(self):
        resp = self.client.post(
            reverse('add_question', args=[self.vform.pk]),
            {'type': 'text'}, HTTP_HX_REQUEST='true',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.vform.questions.count(), 1)

    def test_non_htmx_request_redirects_to_editor(self):
        """Sans HTMX (JS indisponible), l'ajout doit recharger l'éditeur,
        pas renvoyer un fragment de page nu."""
        resp = self.client.post(
            reverse('add_question', args=[self.vform.pk]),
            {'type': 'rating'},
        )
        self.assertEqual(self.vform.questions.count(), 1)
        self.assertRedirects(
            resp, reverse('edit_form', args=[self.vform.pk]),
            fetch_redirect_response=False,
        )


@override_settings(CACHES=LOCMEM_CACHE)
class ResponseSubmissionTests(TestCase):
    """public_form : soumission et validation des réponses."""

    def setUp(self):
        self.owner = User.objects.create_user('owner', password='motdepasse123')
        self.vform = VozaviForm.objects.create(
            user=self.owner, title='Satisfaction', slug='abc123', status='active',
        )
        self.q_rating = Question.objects.create(
            form=self.vform, type='rating', label='Votre note', required=True,
            position=0, options={'max': 5},
        )
        self.q_text = Question.objects.create(
            form=self.vform, type='text', label='Un commentaire ?', required=False,
            position=1, options={},
        )
        self.url = reverse('public_form', args=['abc123'])

    def test_valid_submission_creates_response_and_answers(self):
        resp = self.client.post(self.url, {
            f'q_{self.q_rating.pk}': '4',
            f'q_{self.q_text.pk}': 'Très bon service',
        })

        self.assertEqual(VozaviResponse.objects.count(), 1)
        self.assertEqual(Answer.objects.count(), 2)
        self.assertRedirects(
            resp, reverse('public_form_thanks', args=['abc123']),
            fetch_redirect_response=False,
        )

    def test_missing_required_field_blocks_submission(self):
        resp = self.client.post(self.url, {
            f'q_{self.q_text.pk}': 'Commentaire sans note',
        })

        self.assertEqual(VozaviResponse.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)
        self.assertEqual(resp.status_code, 200)   # ré-affichage avec erreurs

    def test_inactive_form_is_not_reachable(self):
        self.vform.status = 'draft'
        self.vform.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)


class StatsComputationTests(TestCase):
    """_compute_question_stats : agrégats par type de question."""

    def setUp(self):
        self.vform = VozaviForm.objects.create(title='Stats')

    def _q(self, qtype, options):
        return Question.objects.create(
            form=self.vform, type=qtype, label='Q', position=0, options=options,
        )

    def test_rating_average_and_distribution(self):
        q = self._q('rating', {'max': 5})
        stats = _compute_question_stats(q, [5, 4, 4, 3])

        self.assertEqual(stats['count'], 4)
        self.assertEqual(stats['avg'], 4.0)
        self.assertEqual(stats['max'], 5)
        self.assertEqual(sum(d['count'] for d in stats['dist']), 4)
        self.assertEqual(stats['label'], 'Très bien')

    def test_rating_ignores_out_of_range_and_empty(self):
        q = self._q('rating', {'max': 5})
        stats = _compute_question_stats(q, [9, 0, None, 'x'])  # toutes invalides
        self.assertEqual(stats['count'], 0)
        self.assertIsNone(stats['avg'])

    def test_single_choice_counts_and_ordering(self):
        q = self._q('single_choice', {'choices': ['A', 'B']})
        stats = _compute_question_stats(q, ['A', 'A', 'B'])

        self.assertEqual(stats['total_votes'], 3)
        self.assertEqual(stats['choices'][0]['label'], 'A')   # le plus voté en tête
        self.assertEqual(stats['choices'][0]['count'], 2)

    def test_multiple_choice_counts_each_selection(self):
        q = self._q('multiple_choice', {'choices': ['A', 'B', 'C']})
        stats = _compute_question_stats(q, [['A', 'B'], ['A']])
        self.assertEqual(stats['total_votes'], 3)

    def test_text_keeps_only_non_empty(self):
        q = self._q('text', {})
        stats = _compute_question_stats(q, ['Bien', '', '   ', 'Top'])
        self.assertEqual(stats['count'], 2)
        self.assertEqual(stats['texts'], ['Bien', 'Top'])


class OgImageTests(TestCase):
    """Génération des images Open Graph (aperçus de partage)."""

    def test_global_og_image_is_valid_png(self):
        resp = self.client.get(reverse('og_image'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'image/png')
        self.assertTrue(resp.content.startswith(b'\x89PNG'))

    def test_form_og_image_dimensions(self):
        from PIL import Image
        VozaviForm.objects.create(
            title='Chez Léa', slug='resto1', status='active',
            brand_name='Chez Léa', brand_color='#1D9E75',
        )
        resp = self.client.get(reverse('form_og_image', args=['resto1']))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'image/png')
        img = Image.open(io.BytesIO(resp.content))
        self.assertEqual(img.size, (1200, 630))

    def test_form_og_image_404_when_not_active(self):
        VozaviForm.objects.create(title='Brouillon', slug='draft1', status='draft')
        resp = self.client.get(reverse('form_og_image', args=['draft1']))
        self.assertEqual(resp.status_code, 404)


class PublicPagesTests(TestCase):
    """Pages publiques accessibles (dont les nouvelles : blog, aide)."""

    def test_pages_return_200(self):
        for name in ['home', 'blog', 'aide', 'cgu', 'confidentialite', 'contact']:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)


# ════════════════════════════════════════════════════════════════════════════
#  LOT P0 — gestion des formulaires depuis le dashboard
# ════════════════════════════════════════════════════════════════════════════

class FormsListTests(TestCase):
    """forms_list : liste, recherche, filtre, tri, pagination, cloisonnement."""

    def setUp(self):
        self.user = User.objects.create_user('owner', password='motdepasse123')
        self.other = User.objects.create_user('autre', password='motdepasse123')
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('forms_list'))
        self.assertEqual(resp.status_code, 302)  # redirige vers la connexion

    def test_only_shows_own_forms(self):
        VozaviForm.objects.create(user=self.user, title='À moi', status='draft')
        VozaviForm.objects.create(user=self.other, title="D'un autre", status='draft')
        resp = self.client.get(reverse('forms_list'))
        titles = [f.title for f in resp.context['page_obj']]
        self.assertIn('À moi', titles)
        self.assertNotIn("D'un autre", titles)

    def test_search_filters_by_title(self):
        VozaviForm.objects.create(user=self.user, title='Restaurant Le Bon', status='draft')
        VozaviForm.objects.create(user=self.user, title='Boutique mode', status='draft')
        resp = self.client.get(reverse('forms_list'), {'q': 'restaurant'})
        titles = [f.title for f in resp.context['page_obj']]
        self.assertEqual(titles, ['Restaurant Le Bon'])

    def test_status_filter(self):
        VozaviForm.objects.create(user=self.user, title='Actif', slug='a1', status='active')
        VozaviForm.objects.create(user=self.user, title='Brouillon', status='draft')
        resp = self.client.get(reverse('forms_list'), {'status': 'active'})
        titles = [f.title for f in resp.context['page_obj']]
        self.assertEqual(titles, ['Actif'])

    def test_pagination(self):
        for i in range(13):
            VozaviForm.objects.create(user=self.user, title=f'F{i}', status='draft')
        page1 = self.client.get(reverse('forms_list'))
        self.assertEqual(len(page1.context['page_obj']), 12)
        self.assertEqual(page1.context['page_obj'].paginator.num_pages, 2)
        page2 = self.client.get(reverse('forms_list'), {'page': 2})
        self.assertEqual(len(page2.context['page_obj']), 1)


@override_settings(CACHES=LOCMEM_CACHE)
class DeleteFormTests(TestCase):
    """delete_form : confirmation, suppression en cascade, cloisonnement."""

    def setUp(self):
        self.user = User.objects.create_user('owner', password='motdepasse123')
        self.other = User.objects.create_user('autre', password='motdepasse123')
        self.client.force_login(self.user)
        self.vform = VozaviForm.objects.create(user=self.user, title='À supprimer', status='active', slug='del1')
        q = Question.objects.create(form=self.vform, type='text', label='Q', position=0, options={})
        r = VozaviResponse.objects.create(form=self.vform)
        Answer.objects.create(response=r, question=q, value='coucou')

    def test_get_shows_confirmation(self):
        resp = self.client.get(reverse('delete_form', args=[self.vform.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(VozaviForm.objects.count(), 1)  # rien supprimé sur GET

    def test_post_deletes_form_and_cascade(self):
        resp = self.client.post(reverse('delete_form', args=[self.vform.pk]))
        self.assertRedirects(resp, reverse('forms_list'), fetch_redirect_response=False)
        self.assertEqual(VozaviForm.objects.count(), 0)
        self.assertEqual(VozaviResponse.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

    def test_cannot_delete_others_form(self):
        self.client.force_login(self.other)
        resp = self.client.post(reverse('delete_form', args=[self.vform.pk]))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(VozaviForm.objects.count(), 1)


class ToggleStatusTests(TestCase):
    """toggle_form_status : fermeture / réouverture."""

    def setUp(self):
        self.user = User.objects.create_user('owner', password='motdepasse123')
        self.client.force_login(self.user)

    def test_active_becomes_closed(self):
        f = VozaviForm.objects.create(user=self.user, title='F', slug='f1', status='active')
        self.client.post(reverse('toggle_form_status', args=[f.pk]))
        f.refresh_from_db()
        self.assertEqual(f.status, 'closed')

    def test_closed_becomes_active(self):
        f = VozaviForm.objects.create(user=self.user, title='F', slug='f1', status='closed')
        self.client.post(reverse('toggle_form_status', args=[f.pk]))
        f.refresh_from_db()
        self.assertEqual(f.status, 'active')

    def test_draft_stays_draft(self):
        f = VozaviForm.objects.create(user=self.user, title='F', status='draft')
        self.client.post(reverse('toggle_form_status', args=[f.pk]))
        f.refresh_from_db()
        self.assertEqual(f.status, 'draft')

    def test_get_not_allowed(self):
        f = VozaviForm.objects.create(user=self.user, title='F', slug='f1', status='active')
        self.assertEqual(self.client.get(reverse('toggle_form_status', args=[f.pk])).status_code, 405)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(TestCase):
    """Flux complet de réinitialisation de mot de passe (mot de passe oublié)."""

    def test_pages_render(self):
        for name in ['password_reset', 'password_reset_done', 'password_reset_complete']:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_full_reset_flow_changes_password(self):
        from django.core import mail
        import re

        User.objects.create_user('jean', email='jean@exemple.com', password='ancien123')

        # 1. Demande de réinitialisation → e-mail envoyé
        self.client.post(reverse('password_reset'), {'email': 'jean@exemple.com'})
        self.assertEqual(len(mail.outbox), 1)

        # 2. Extraction du lien de confirmation depuis l'e-mail
        link = re.search(r'/mot-de-passe/reinitialiser/[^\s]+/[^\s/]+/', mail.outbox[0].body)
        self.assertIsNotNone(link)
        confirm_url = link.group(0)

        # 3. Le GET redirige vers l'URL 'set-password' (jeton validé en session)
        resp = self.client.get(confirm_url)
        self.assertEqual(resp.status_code, 302)

        # 4. Définition du nouveau mot de passe
        resp = self.client.post(resp.url, {
            'new_password1': 'NouveauMdp2026',
            'new_password2': 'NouveauMdp2026',
        })
        self.assertRedirects(resp, reverse('password_reset_complete'), fetch_redirect_response=False)

        # 5. Le nouveau mot de passe fonctionne
        user = User.objects.get(username='jean')
        self.assertTrue(user.check_password('NouveauMdp2026'))


# ════════════════════════════════════════════════════════════════════════════
#  LOT P1 — expérience & rétention
# ════════════════════════════════════════════════════════════════════════════

LOCMEM_EMAIL = 'django.core.mail.backends.locmem.EmailBackend'


@override_settings(EMAIL_BACKEND=LOCMEM_EMAIL)
class NewResponseNotificationTests(TestCase):
    """Notification e-mail au créateur (logique d'envoi)."""

    def setUp(self):
        from . import tasks
        self.send = tasks.send_new_response_email
        self.user = User.objects.create_user('o', email='o@x.co', password='motdepasse123')

    def test_email_sent_when_enabled(self):
        from django.core import mail
        f = VozaviForm.objects.create(user=self.user, title='Resto', slug='r1',
                                      status='active', notify_responses=True)
        VozaviResponse.objects.create(form=f)
        self.send(f.pk, 'http://x/results')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['o@x.co'])
        self.assertIn('Resto', mail.outbox[0].subject)

    def test_no_email_when_disabled(self):
        from django.core import mail
        f = VozaviForm.objects.create(user=self.user, title='Resto', slug='r1',
                                      status='active', notify_responses=False)
        self.send(f.pk, 'http://x/results')
        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_for_guest_form(self):
        from django.core import mail
        f = VozaviForm.objects.create(user=None, title='Invité', slug='g1',
                                      status='active', notify_responses=True)
        self.send(f.pk, 'http://x/results')
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(CACHES=LOCMEM_CACHE)
    def test_submission_triggers_email(self):
        """Soumission publique → e-mail (after_response forcé en mode immédiat)."""
        import after_response.decorators as ard
        from django.core import mail
        f = VozaviForm.objects.create(user=self.user, title='Resto', slug='r1',
                                      status='active', notify_responses=True)
        q = Question.objects.create(form=f, type='text', label='Avis', required=True,
                                    position=0, options={})
        old = ard.AFTER_RESPONSE_IMMEDIATE
        ard.AFTER_RESPONSE_IMMEDIATE = True
        try:
            self.client.post(reverse('public_form', args=['r1']), {f'q_{q.pk}': 'Top'})
        finally:
            ard.AFTER_RESPONSE_IMMEDIATE = old
        self.assertEqual(len(mail.outbox), 1)

    def test_toggle_endpoint(self):
        self.client.force_login(self.user)
        f = VozaviForm.objects.create(user=self.user, title='F', slug='f1', status='active')
        self.client.post(reverse('update_form_notify', args=[f.pk]), {})  # case décochée
        f.refresh_from_db()
        self.assertFalse(f.notify_responses)
        self.client.post(reverse('update_form_notify', args=[f.pk]), {'notify_responses': 'on'})
        f.refresh_from_db()
        self.assertTrue(f.notify_responses)


class AccountSettingsTests(TestCase):
    """account_settings + delete_account."""

    def setUp(self):
        self.user = User.objects.create_user('jean', email='jean@x.co', password='ancien123')
        self.client.force_login(self.user)

    def test_change_email(self):
        self.client.post(reverse('account_settings'), {'action': 'email', 'email': 'NEW@x.co'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@x.co')

    def test_change_email_rejects_duplicate(self):
        User.objects.create_user('autre', email='pris@x.co', password='x123456789')
        self.client.post(reverse('account_settings'), {'action': 'email', 'email': 'pris@x.co'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'jean@x.co')  # inchangé

    def test_change_password_keeps_session(self):
        resp = self.client.post(reverse('account_settings'), {
            'action': 'password', 'current_password': 'ancien123',
            'new_password1': 'Nouveau12345', 'new_password2': 'Nouveau12345',
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Nouveau12345'))
        # toujours connecté après le changement
        self.assertEqual(self.client.get(reverse('account_settings')).status_code, 200)

    def test_change_password_wrong_current(self):
        self.client.post(reverse('account_settings'), {
            'action': 'password', 'current_password': 'FAUX',
            'new_password1': 'Nouveau12345', 'new_password2': 'Nouveau12345',
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ancien123'))  # inchangé

    def test_delete_account_requires_correct_password(self):
        self.client.post(reverse('delete_account'), {'password': 'FAUX'})
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_account_success(self):
        resp = self.client.post(reverse('delete_account'), {'password': 'ancien123'})
        self.assertRedirects(resp, reverse('home'), fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())


class DuplicateFormTests(TestCase):
    """duplicate_form : copie en brouillon avec questions."""

    def setUp(self):
        self.user = User.objects.create_user('o', password='motdepasse123')
        self.other = User.objects.create_user('autre', password='motdepasse123')
        self.client.force_login(self.user)
        self.vform = VozaviForm.objects.create(user=self.user, title='Original',
                                               slug='orig', status='active', notify_responses=True)
        Question.objects.create(form=self.vform, type='rating', label='Note',
                                required=True, position=0, options={'max': 5})
        Question.objects.create(form=self.vform, type='text', label='Commentaire',
                                required=False, position=1, options={})

    def test_duplicate_copies_questions_as_draft(self):
        resp = self.client.post(reverse('duplicate_form', args=[self.vform.pk]))
        self.assertEqual(resp.status_code, 302)
        copy = VozaviForm.objects.exclude(pk=self.vform.pk).get()
        self.assertEqual(copy.status, 'draft')
        self.assertIsNone(copy.slug)
        self.assertIn('copie', copy.title)
        self.assertEqual(copy.questions.count(), 2)

    def test_cannot_duplicate_others_form(self):
        self.client.force_login(self.other)
        resp = self.client.post(reverse('duplicate_form', args=[self.vform.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_get_not_allowed(self):
        self.assertEqual(
            self.client.get(reverse('duplicate_form', args=[self.vform.pk])).status_code, 405)


@override_settings(CACHES=LOCMEM_CACHE)
class ResultsTrendTests(TestCase):
    """form_results : série d'activité sur 14 jours."""

    def setUp(self):
        self.user = User.objects.create_user('o', password='motdepasse123')
        self.client.force_login(self.user)
        self.vform = VozaviForm.objects.create(user=self.user, title='F', slug='f1', status='active')
        Question.objects.create(form=self.vform, type='text', label='Q', required=False,
                                position=0, options={})
        VozaviResponse.objects.create(form=self.vform)

    def test_trend_in_context(self):
        resp = self.client.get(reverse('form_results', args=[self.vform.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['daily_series']), 14)
        # la réponse créée aujourd'hui compte dans la semaine
        self.assertEqual(resp.context['last_7'], 1)


class ShareChannelsTests(TestCase):
    """share_form : page de partage avec canaux (WhatsApp...)."""

    def setUp(self):
        self.user = User.objects.create_user('o', password='motdepasse123')
        self.client.force_login(self.user)

    def test_share_page_has_whatsapp(self):
        f = VozaviForm.objects.create(user=self.user, title='F', slug='f1', status='active')
        resp = self.client.get(reverse('share_form', args=[f.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'wa.me')
        self.assertContains(resp, 'Envoyer par WhatsApp')
        self.assertContains(resp, 'Donnez%20votre%20avis')  # message pré-rempli (URL-encodé)


class OnboardingWelcomeTests(TestCase):
    """Onboarding : redirection après inscription + en-tête de bienvenue."""

    def test_signup_redirects_to_welcome(self):
        resp = self.client.post(reverse('signup'), {
            'username': 'nouveau',
            'email': 'nouveau@example.com',
            'password1': 'motdepasse123',
        })
        self.assertRedirects(
            resp, reverse('new_form') + '?bienvenue=1',
            fetch_redirect_response=False,
        )
