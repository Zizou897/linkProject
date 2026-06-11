import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Lookup a dict value by key (supports string coercion)."""
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key) or dictionary.get(str(key))


@register.filter
def to_json(value):
    """Serialize a Python value to a JSON string (safe for inline Alpine.js)."""
    return mark_safe(json.dumps(value, ensure_ascii=False))


@register.simple_tag
def get_contact_fields():
    return [
        {'key': 'first_name', 'label': 'Prénom',          'input_type': 'text',  'placeholder': 'Votre prénom'},
        {'key': 'last_name',  'label': 'Nom',              'input_type': 'text',  'placeholder': 'Votre nom'},
        {'key': 'email',      'label': 'Adresse e-mail',   'input_type': 'email', 'placeholder': 'votre@email.com'},
        {'key': 'phone',      'label': 'Téléphone',         'input_type': 'tel',   'placeholder': '+225 07 00 00 00'},
        {'key': 'company',    'label': 'Entreprise',        'input_type': 'text',  'placeholder': 'Nom de votre entreprise'},
        {'key': 'job_title',  'label': 'Poste / Fonction',  'input_type': 'text',  'placeholder': 'Votre poste'},
    ]
