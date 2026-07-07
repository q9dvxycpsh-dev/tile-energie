"""Logique métier centrale de la plateforme.

Estimation indicative du coût, recherche de techniciens par proximité,
affectation automatique et transitions de statut. Regroupé ici pour que les
vues restent fines et que les règles du cahier des charges soient à un seul
endroit.
"""
from django.utils import timezone

from accounts.models import TechnicianProfile
from .models import (ACTIVE_STATUSES, ActivityLog, Mission, Notification,
                     Status)

# Coût de base indicatif par type de service (FCFA)
BASE_COST = {
    'installation-panneaux': 40000,
    'reparation-batteries': 25000,
    'maintenance-onduleurs': 20000,
    'diagnostic-pannes': 10000,
    'conseil-optimisation': 8000,
}
URGENCY_FACTOR = {'faible': 0.9, 'normale': 1.0, 'haute': 1.2, 'urgente': 1.5}


def estimate_cost(skill, urgency='normale'):
    base = BASE_COST.get(getattr(skill, 'slug', None), 15000)
    factor = URGENCY_FACTOR.get(urgency, 1.0)
    raw = base * factor
    return int(round(raw / 500.0) * 500)


def nearby_technicians(request, limit=8):
    """Techniciens validés et disponibles, triés par proximité puis par note.

    Règle métier : un technicien non validé ne peut pas être affecté.
    """
    qs = TechnicianProfile.objects.filter(
        verification=TechnicianProfile.Verification.VERIFIED,
        user__is_suspended=False,
    ).select_related('user').prefetch_related('skills')

    if request.skill_id:
        qs = qs.filter(skills=request.skill).distinct()

    techs = list(qs)
    for t in techs:
        t.distance = t.distance_km(request.lat, request.lng)
    available = [t for t in techs if t.is_available]
    pool = available or techs

    def sort_key(t):
        return (t.distance if t.distance is not None else 9999, -t.rating_avg)

    pool.sort(key=sort_key)
    return pool[:limit]


def auto_assign(request, actor=None):
    """Affecte le meilleur technicien proche et crée la mission.

    Se base sur la proximité, la disponibilité et les compétences déclarées,
    conformément au cahier des charges. Retourne la Mission ou None.
    """
    if hasattr(request, 'mission_obj'):
        return request.mission_obj
    candidates = nearby_technicians(request, limit=1)
    if not candidates:
        request.status = Status.EN_ATTENTE
        request.save(update_fields=['status', 'updated_at'])
        request.log(Status.EN_ATTENTE, actor=actor, note='Aucun technicien disponible pour le moment')
        return None
    tech = candidates[0]
    mission = Mission.objects.create(
        request=request, technician=tech, status=Status.ACCEPTEE,
        accepted_at=timezone.now(), tech_lat=tech.current_lat, tech_lng=tech.current_lng,
        final_cost=request.estimated_cost,
    )
    tech.availability = TechnicianProfile.Availability.BUSY
    tech.save(update_fields=['availability'])
    request.status = Status.ACCEPTEE
    request.save(update_fields=['status', 'updated_at'])
    request.log(Status.ACCEPTEE, actor=actor, note=f'Affecté à {tech.user.display_name}')
    Notification.push(request.client, 'Technicien affecté',
                      f'{tech.user.display_name} prend en charge votre demande {request.reference}.',
                      url=f'/app/client/demande/{request.id}/', icon='check')
    Notification.push(tech.user, 'Nouvelle mission',
                      f'Demande {request.reference} à {request.address or "votre zone"}.',
                      url=f'/app/technicien/mission/{mission.id}/', icon='bolt')
    ActivityLog.record(actor, 'Affectation automatique', f'{request.reference} → {tech.user.display_name}')
    return mission


# Transitions autorisées côté technicien
MISSION_FLOW = {
    Status.ACCEPTEE: Status.EN_ROUTE,
    Status.EN_ROUTE: Status.SUR_SITE,
    Status.SUR_SITE: Status.TERMINEE,
}

STATUS_TIMESTAMP = {
    Status.EN_ROUTE: 'en_route_at',
    Status.SUR_SITE: 'on_site_at',
    Status.TERMINEE: 'completed_at',
}


def advance_mission(mission, new_status, actor=None):
    """Applique une transition de statut, horodate, miroir sur la demande,
    historise et notifie le client. Chaque changement est enregistré."""
    mission.status = new_status
    field = STATUS_TIMESTAMP.get(new_status)
    if field and getattr(mission, field) is None:
        setattr(mission, field, timezone.now())
    mission.save()

    req = mission.request
    req.status = new_status
    req.save(update_fields=['status', 'updated_at'])
    req.log(new_status, actor=actor)

    tech = mission.technician
    if new_status == Status.TERMINEE:
        tech.availability = TechnicianProfile.Availability.AVAILABLE
        tech.completed_missions = tech.completed_missions + 1
        tech.save(update_fields=['availability', 'completed_missions'])

    labels = {
        Status.EN_ROUTE: 'Votre technicien est en route',
        Status.SUR_SITE: 'Votre technicien est arrivé sur site',
        Status.TERMINEE: 'Intervention terminée',
    }
    if new_status in labels:
        Notification.push(req.client, labels[new_status],
                          f'Demande {req.reference}.',
                          url=f'/app/client/demande/{req.id}/', icon='bolt')
    ActivityLog.record(actor, f'Statut → {new_status}', req.reference)
    return mission


def cancel_request(request, actor=None, note='Annulée par le client'):
    request.status = Status.ANNULEE
    request.save(update_fields=['status', 'updated_at'])
    request.log(Status.ANNULEE, actor=actor, note=note)
    mission = getattr(request, 'mission_obj', None)
    if mission:
        mission.status = Status.ANNULEE
        mission.cancelled_at = timezone.now()
        mission.save(update_fields=['status', 'cancelled_at'])
        tech = mission.technician
        tech.availability = TechnicianProfile.Availability.AVAILABLE
        tech.save(update_fields=['availability'])
    ActivityLog.record(actor, 'Annulation', request.reference)


def recompute_rating(technician):
    from .models import Review
    reviews = Review.objects.filter(mission__technician=technician)
    count = reviews.count()
    if count:
        avg = sum(r.rating for r in reviews) / count
        technician.rating_avg = round(avg, 1)
        technician.rating_count = count
        technician.save(update_fields=['rating_avg', 'rating_count'])
