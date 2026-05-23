"""
Commande de chargement des données de démonstration.
Usage : python manage.py load_demo_data [--reset]
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from app.models import Formation, LienSecurise, SessionPresentielle, Avis


FORMATIONS = [
    {
        "libelle": "Gestion de projet avec les outils agiles",
        "descriptif": "Maîtrisez les méthodes Scrum et Kanban pour piloter vos projets avec efficacité. Cette formation couvre la planification, le suivi des sprints et la gestion des parties prenantes.",
        "objectifs_pedagogiques": "Comprendre le manifeste Agile, animer des cérémonies Scrum, utiliser un tableau Kanban, gérer un backlog produit, produire des indicateurs de suivi.",
    },
    {
        "libelle": "Communication institutionnelle et prise de parole en public",
        "descriptif": "Développez votre aisance à l'oral, structurez vos messages et renforcez l'image de votre organisation lors de prises de parole officielles.",
        "objectifs_pedagogiques": "Structurer un discours, maîtriser la communication non verbale, gérer le stress, conduire une conférence de presse, rédiger des communiqués.",
    },
    {
        "libelle": "Analyse de données avec Excel et Power BI",
        "descriptif": "Transformez vos données brutes en tableaux de bord dynamiques. Apprenez à nettoyer, analyser et visualiser des données métier pour une prise de décision éclairée.",
        "objectifs_pedagogiques": "Maîtriser les formules avancées Excel, créer des tableaux croisés dynamiques, connecter des sources de données Power BI, publier des rapports interactifs.",
    },
    {
        "libelle": "Management d'équipe et leadership situationnel",
        "descriptif": "Renforcez vos compétences managériales en apprenant à adapter votre style de leadership au profil et au niveau de maturité de chaque collaborateur.",
        "objectifs_pedagogiques": "Identifier son style de management, motiver ses équipes, conduire des entretiens de performance, gérer les conflits, déléguer efficacement.",
    },
    {
        "libelle": "Passation des marchés publics au Cameroun",
        "descriptif": "Maîtrisez le cadre réglementaire camerounais des marchés publics : préparation des dossiers d'appel d'offres, analyse des offres, attribution et exécution des marchés.",
        "objectifs_pedagogiques": "Connaître le code des marchés publics, préparer un DAO, analyser les offres techniques et financières, rédiger les actes contractuels, gérer les litiges.",
    },
    {
        "libelle": "Rédaction administrative et professionnelle",
        "descriptif": "Perfectionnez votre maîtrise des écrits professionnels : notes de service, rapports, comptes rendus, courriers officiels et correspondance administrative.",
        "objectifs_pedagogiques": "Appliquer les règles de la correspondance officielle, rédiger des rapports structurés, maîtriser le style administratif, éviter les fautes courantes.",
    },
    {
        "libelle": "Gestion des ressources humaines et droit du travail",
        "descriptif": "Acquérez les fondamentaux de la gestion RH et du droit du travail camerounais pour sécuriser vos pratiques et accompagner vos collaborateurs.",
        "objectifs_pedagogiques": "Gérer les contrats de travail, calculer les congés et la paie, conduire des entretiens RH, gérer les départs, appliquer le Code du travail.",
    },
    {
        "libelle": "Comptabilité générale et gestion financière",
        "descriptif": "Formation pratique aux fondements de la comptabilité OHADA et aux outils d'analyse financière pour piloter la santé économique de votre structure.",
        "objectifs_pedagogiques": "Tenir une comptabilité OHADA, établir un bilan et un compte de résultat, analyser des ratios financiers, gérer la trésorerie.",
    },
]

SESSIONS = [
    {
        "formation_idx": 0,
        "date": date.today() + timedelta(days=18),
        "lieu": "Hôtel Hilton, Yaoundé — Salle Conférence A",
        "formateur": "Dr. Emmanuel NGONO",
        "capacite": 20,
        "duree": "3 jours",
        "cout": None,
        "public_cible": "Chefs de projet, coordinateurs, responsables d'équipe.",
        "periode_previsionnelle": "Juin 2026",
        "statut": "planifiee",
        "lien_actif": True,
    },
    {
        "formation_idx": 1,
        "date": date.today() + timedelta(days=45),
        "lieu": "Centre de formation Bediakon, Douala",
        "formateur": "Mme Christelle ATANGANA",
        "capacite": 15,
        "duree": "2 jours",
        "cout": 150000,
        "public_cible": "Directeurs, responsables de la communication, cadres exposés aux médias.",
        "periode_previsionnelle": "Juillet 2026",
        "statut": "planifiee",
        "lien_actif": True,
    },
    {
        "formation_idx": 2,
        "date": date.today() - timedelta(days=12),
        "lieu": "Hôtel Akwa Palace, Douala — Salle Bali",
        "formateur": "M. Patrick ESSOMBA",
        "capacite": 18,
        "duree": "4 jours",
        "cout": 200000,
        "public_cible": "Contrôleurs de gestion, responsables financiers, analystes.",
        "periode_previsionnelle": "Septembre 2026",
        "statut": "cloturee",
        "lien_actif": False,
    },
    {
        "formation_idx": 4,
        "date": date.today() + timedelta(days=60),
        "lieu": "Centre Polyvalente de Yaoundé",
        "formateur": "M. Théodore MVONDO",
        "capacite": 25,
        "duree": "5 jours",
        "cout": 250000,
        "public_cible": "Agents des services des marchés publics, responsables administratifs.",
        "periode_previsionnelle": "Octobre 2026",
        "statut": "planifiee",
        "lien_actif": True,
    },
]

AVIS_DATA = [
    {
        "nom": "MBARGA", "prenom": "Serge",
        "structure": "Ministère de la Santé Publique", "fonction": "Responsable de projet",
        "email": "s.mbarga@sante.cm", "telephone": "+237 677 001 234",
        "zone_geographique": "Yaoundé",
        "motivations": "Je souhaite acquérir des compétences pratiques en analyse de données pour améliorer le suivi des indicateurs de santé dans notre département.",
        "probleme_professionnel": "Nous gérons des volumes importants de données épidémiologiques sans outils adaptés pour les synthétiser.",
        "competences_attendues": "Créer des tableaux de bord automatisés, maîtriser Power BI pour les rapports mensuels.",
        "contraintes_calendrier": "",
        "contrainte_mobilite": False,
        "format_prefere": "presentiel",
        "observation": "Formation très pertinente pour notre équipe.",
    },
    {
        "nom": "FOUDA", "prenom": "Martine",
        "structure": "Groupe Sabc", "fonction": "Contrôleur de gestion",
        "email": "m.fouda@sabc.cm", "telephone": "+237 699 456 789",
        "zone_geographique": "Douala",
        "motivations": "Améliorer mes capacités de reporting financier et réduire le temps de préparation des tableaux de bord mensuels.",
        "probleme_professionnel": "Les fichiers Excel deviennent trop lourds et complexes à maintenir pour notre équipe.",
        "competences_attendues": "Power BI, connexion aux bases de données ERP, automatisation des rapports.",
        "contraintes_calendrier": "Pas disponible en août",
        "contrainte_mobilite": False,
        "format_prefere": "hybride",
        "observation": "",
    },
    {
        "nom": "NKOLO", "prenom": "Jean-Baptiste",
        "structure": "ONG Cameroun Développement", "fonction": "Coordinateur de programmes",
        "email": "jb.nkolo@camd.org", "telephone": "+237 655 321 987",
        "zone_geographique": "Yaoundé",
        "motivations": "Notre ONG doit rendre des comptes aux bailleurs sur l'impact de nos projets. J'ai besoin d'outils pour visualiser nos données terrain.",
        "probleme_professionnel": "Nos rapports d'impact sont encore manuels et peu visuels.",
        "competences_attendues": "Visualisation de données, cartes et graphiques interactifs.",
        "contraintes_calendrier": "",
        "contrainte_mobilite": True,
        "format_prefere": "distanciel",
        "observation": "Je préfère une formation en ligne si possible.",
    },
    {
        "nom": "TALLA", "prenom": "Armelle",
        "structure": "Banque Atlantique Cameroun", "fonction": "Analyste risque",
        "email": "a.talla@ba-cameroun.com", "telephone": "+237 691 112 233",
        "zone_geographique": "Douala",
        "motivations": "Renforcer mes compétences analytiques pour mieux modéliser les risques de crédit et améliorer nos rapports réglementaires.",
        "probleme_professionnel": "Nos modèles Excel atteignent leurs limites avec la croissance du portefeuille.",
        "competences_attendues": "Power Query, modélisation de données, Power BI Service.",
        "contraintes_calendrier": "",
        "contrainte_mobilite": False,
        "format_prefere": "presentiel",
        "observation": "",
    },
    {
        "nom": "BEYEME", "prenom": "Rodrigue",
        "structure": "Mairie de Bafoussam", "fonction": "Chef service informatique",
        "email": "r.beyeme@bafoussam.cm", "telephone": "+237 677 889 000",
        "zone_geographique": "Bafoussam",
        "motivations": "Moderniser le suivi budgétaire de la commune avec des outils de visualisation adaptés aux décideurs locaux.",
        "probleme_professionnel": "Les élus locaux ont du mal à lire les tableaux Excel standards.",
        "competences_attendues": "Tableaux de bord exécutifs, indicateurs KPI communaux.",
        "contraintes_calendrier": "Préférence pour les sessions du vendredi au dimanche",
        "contrainte_mobilite": True,
        "format_prefere": "hybride",
        "observation": "Intéressé pour une session in-situ à Bafoussam si possible.",
    },
    {
        "nom": "ONANA", "prenom": "Carine",
        "structure": "Cameroon Airlines Corporation", "fonction": "Responsable RH",
        "email": "c.onana@camair-co.cm", "telephone": "+237 699 445 566",
        "zone_geographique": "Yaoundé",
        "motivations": "Automatiser le suivi des effectifs et des congés, produire des indicateurs RH clairs pour la direction.",
        "probleme_professionnel": "Nos données RH sont dispersées dans plusieurs fichiers non consolidés.",
        "competences_attendues": "Power BI, consolidation de sources multiples, tableaux de bord RH.",
        "contraintes_calendrier": "",
        "contrainte_mobilite": False,
        "format_prefere": "presentiel",
        "observation": "",
    },
    {
        "nom": "NDOUMBE", "prenom": "Hervé",
        "structure": "Total Energies Cameroun", "fonction": "Ingénieur production",
        "email": "h.ndoumbe@totalenergies.cm", "telephone": "+237 655 778 899",
        "zone_geographique": "Douala",
        "motivations": "Exploiter les données de production de nos installations pour anticiper les pannes et optimiser la maintenance.",
        "probleme_professionnel": "Nous collectons beaucoup de données capteurs mais sans outil d'analyse adapté.",
        "competences_attendues": "Importation de données CSV/Excel, Power BI, alertes automatiques.",
        "contraintes_calendrier": "Pas disponible en décembre",
        "contrainte_mobilite": False,
        "format_prefere": "presentiel",
        "observation": "",
    },
    {
        "nom": "ATEBA", "prenom": "Nadège",
        "structure": "CAMPOST", "fonction": "Directrice adjointe finances",
        "email": "n.ateba@campost.cm", "telephone": "+237 677 334 455",
        "zone_geographique": "Yaoundé",
        "motivations": "Produire des rapports financiers consolidés pour le Conseil d'Administration avec des visuels percutants.",
        "probleme_professionnel": "La consolidation mensuelle prend 3 jours à mon équipe alors que les données sont déjà disponibles.",
        "competences_attendues": "Automatisation des rapports, actualisation planifiée, partage sécurisé.",
        "contraintes_calendrier": "",
        "contrainte_mobilite": False,
        "format_prefere": "presentiel",
        "observation": "Très intéressée, j'aimerais aussi une formation pour mon équipe.",
    },
]


class Command(BaseCommand):
    help = "Charge les données de démonstration pour la présentation."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Supprime toutes les données existantes avant le chargement.'
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING("Suppression des données existantes..."))
            Avis.objects.all().delete()
            SessionPresentielle.objects.all().delete()
            LienSecurise.objects.all().delete()
            Formation.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Données supprimées."))

        # ── Formations ────────────────────────────────────────────
        self.stdout.write("Création des formations...")
        formations = []
        for data in FORMATIONS:
            f = Formation.objects.create(**data)
            formations.append(f)
        self.stdout.write(self.style.SUCCESS(f"  {len(formations)} formations créées."))

        # ── Sessions ──────────────────────────────────────────────
        self.stdout.write("Création des sessions...")
        sessions = []
        for s_data in SESSIONS:
            formation = formations[s_data.pop("formation_idx")]
            lien_actif = s_data.pop("lien_actif")
            lien_session = LienSecurise.objects.create(
                label=f"Session — {formation.libelle} ({s_data['date'].strftime('%d/%m/%Y')})",
                actif=lien_actif,
                date_expiration=timezone.now() + timedelta(days=90) if lien_actif else None,
            )
            session = SessionPresentielle.objects.create(
                formation=formation,
                lien=lien_session,
                **s_data,
            )
            sessions.append(session)
        self.stdout.write(self.style.SUCCESS(f"  {len(sessions)} sessions créées."))

        # ── Avis (sur la session clôturée = sessions[2]) ──────────
        self.stdout.write("Création des avis...")
        session_cloturee = sessions[2]
        for a_data in AVIS_DATA:
            Avis.objects.create(session=session_cloturee, **a_data)
        self.stdout.write(self.style.SUCCESS(f"  {len(AVIS_DATA)} avis créés."))

        # ── Résumé ────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("✓ Données de démonstration chargées avec succès !"))
        self.stdout.write(f"  • {Formation.objects.count()} formations")
        self.stdout.write(f"  • {SessionPresentielle.objects.count()} sessions")
        self.stdout.write(f"  • {Avis.objects.count()} avis")
        self.stdout.write(f"  • {LienSecurise.objects.count()} liens sécurisés")
