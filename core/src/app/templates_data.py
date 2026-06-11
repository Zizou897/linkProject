FORM_TEMPLATES = {
    'restaurant': {
        'title': 'Avis clients',
        'questions': [
            {'type': 'rating', 'label': 'Comment évaluez-vous votre expérience globale ?', 'required': True, 'options': {'max': 5}},
            {'type': 'single_choice', 'label': 'Quel repas avez-vous pris ?', 'required': False, 'options': {'choices': ['Petit-déjeuner', 'Déjeuner', 'Dîner']}},
            {'type': 'grid', 'label': 'Évaluez les aspects suivants', 'required': False, 'options': {'criteria': ["La qualité des plats", "Le service", "L'ambiance", "Le rapport qualité/prix"], 'max': 5}},
            {'type': 'text', 'label': 'Un commentaire ou suggestion ?', 'required': False, 'options': {}},
        ]
    },
    'service': {
        'title': 'Satisfaction après prestation',
        'questions': [
            {'type': 'rating', 'label': 'Êtes-vous satisfait(e) de notre prestation ?', 'required': True, 'options': {'max': 5}},
            {'type': 'grid', 'label': 'Évaluez les critères suivants', 'required': False, 'options': {'criteria': ["La qualité du travail", "Le respect des délais", "La communication", "Le rapport qualité/prix"], 'max': 5}},
            {'type': 'single_choice', 'label': 'Recommanderiez-vous nos services ?', 'required': False, 'options': {'choices': ['Oui, certainement', 'Probablement', 'Non']}},
            {'type': 'text', 'label': "Avez-vous des suggestions d'amélioration ?", 'required': False, 'options': {}},
        ]
    },
    'boutique': {
        'title': 'Avis boutique',
        'questions': [
            {'type': 'rating', 'label': "Comment évaluez-vous votre expérience d'achat ?", 'required': True, 'options': {'max': 5}},
            {'type': 'grid', 'label': 'Évaluez les aspects suivants', 'required': False, 'options': {'criteria': ["L'accueil", "La disponibilité des produits", "Les prix", "La propreté"], 'max': 5}},
            {'type': 'single_choice', 'label': 'Reviendrez-vous dans notre boutique ?', 'required': False, 'options': {'choices': ['Oui, certainement', 'Probablement', 'Non']}},
            {'type': 'text', 'label': 'Un commentaire libre ?', 'required': False, 'options': {}},
        ]
    },
    'livraison': {
        'title': 'Satisfaction après livraison',
        'questions': [
            {'type': 'rating', 'label': 'Êtes-vous satisfait(e) de votre livraison ?', 'required': True, 'options': {'max': 5}},
            {'type': 'single_choice', 'label': 'Votre colis est-il arrivé en bon état ?', 'required': False, 'options': {'choices': ['Oui, parfait', 'Quelques dommages mineurs', 'Endommagé']}},
            {'type': 'single_choice', 'label': 'La livraison a-t-elle été effectuée dans les délais ?', 'required': False, 'options': {'choices': ['Oui, à temps', 'Légèrement en retard', 'Très en retard']}},
            {'type': 'text', 'label': 'Un commentaire sur votre livraison ?', 'required': False, 'options': {}},
        ]
    },
    'employes': {
        'title': 'Feedback équipe interne',
        'questions': [
            {'type': 'rating', 'label': 'Comment évaluez-vous votre satisfaction au travail ?', 'required': True, 'options': {'max': 5}},
            {'type': 'grid', 'label': 'Évaluez les aspects suivants', 'required': False, 'options': {'criteria': ["L'ambiance d'équipe", "La communication interne", "La charge de travail", "La reconnaissance"], 'max': 5}},
            {'type': 'single_choice', 'label': 'Recommanderiez-vous cette entreprise comme employeur ?', 'required': False, 'options': {'choices': ['Oui', 'Peut-être', 'Non']}},
            {'type': 'text', 'label': "Vos suggestions pour améliorer l'environnement de travail", 'required': False, 'options': {}},
        ]
    },
    'scratch': {
        'title': 'Donnez votre avis',
        'questions': [
            {'type': 'rating', 'label': 'Quelle note donneriez-vous ?', 'required': True, 'options': {'max': 5}},
            {'type': 'text', 'label': 'Avez-vous des commentaires ?', 'required': False, 'options': {}},
        ]
    },
}
