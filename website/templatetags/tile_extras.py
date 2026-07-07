"""Filtres et tags réutilisables du design system TILE ÉNERGIE."""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def icon(name, cls=''):
    """Insère une icône SVG du sprite. Aucun emoji n'est utilisé sur le site."""
    classes = ('icon ' + cls).strip()
    return mark_safe(
        f'<svg class="{classes}" aria-hidden="true" focusable="false">'
        f'<use href="#i-{name}"></use></svg>'
    )


@register.filter
def fcfa(value):
    """Formate un entier en montant FCFA avec séparateur d'espace fine."""
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return value
    s = f'{n:,}'.replace(',', ' ')
    return mark_safe(f'{s} FCFA')


@register.filter
def money(value):
    """Nombre formaté avec séparateurs, sans devise."""
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return value
    return f'{n:,}'.replace(',', ' ')


@register.filter
def tone_class(tone):
    return f'badge--{tone}'


@register.filter
def get_item(d, key):
    try:
        return d.get(key)
    except AttributeError:
        return None


@register.filter
def to_stars(rating):
    """Renvoie une liste de 5 éléments 'full' / 'empty' pour afficher une note."""
    try:
        r = int(round(float(rating)))
    except (TypeError, ValueError):
        r = 0
    r = max(0, min(5, r))
    return ['full'] * r + ['empty'] * (5 - r)
