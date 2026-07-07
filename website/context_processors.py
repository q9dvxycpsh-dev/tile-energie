"""Contexte global injecté dans tous les gabarits."""
from django.conf import settings


def site(request):
    ctx = {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_BASELINE': settings.SITE_BASELINE,
        'MAP_CENTER': settings.DEFAULT_MAP_CENTER,
    }
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        from interventions.models import Notification
        ctx['nav_notifs'] = list(Notification.objects.filter(user=user)[:8])
        ctx['nav_notif_unread'] = Notification.objects.filter(user=user, is_read=False).count()
        if user.is_platform_admin:
            ctx['dashboard_url'] = 'interventions:admin_dashboard'
            ctx['role_label'] = 'Administration'
        elif user.is_technicien:
            ctx['dashboard_url'] = 'interventions:tech_dashboard'
            ctx['role_label'] = 'Espace technicien'
        else:
            ctx['dashboard_url'] = 'interventions:client_dashboard'
            ctx['role_label'] = 'Espace client'
    return ctx
