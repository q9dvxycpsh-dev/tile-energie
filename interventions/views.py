"""Vues de la plateforme : espaces client, technicien et administration,
plus les API JSON qui alimentent les cartes en temps réel.
"""
import math
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import Skill, TechnicianProfile
from .forms import (DisputeForm, PaymentForm, RequestForm, ReviewForm,
                    TechnicianDocumentForm)
from .models import (ACTIVE_STATUSES, ActivityLog, Dispute, InterventionRequest,
                     Mission, Notification, Payment, RequestPhoto, Review,
                     Status, TRACKING_STEPS)
from . import services

User = get_user_model()


# --------------------------------------------------------------------------
# Contrôle d'accès par rôle
# --------------------------------------------------------------------------
def role_required(check):
    def deco(view):
        @wraps(view)
        @login_required
        def wrapped(request, *args, **kwargs):
            if not check(request.user):
                messages.error(request, "Cet espace n'est pas accessible avec votre profil.")
                return redirect('accounts:redirect_after_login')
            return view(request, *args, **kwargs)
        return wrapped
    return deco


client_required = role_required(lambda u: u.is_client)
tech_required = role_required(lambda u: u.is_technicien and hasattr(u, 'technician_profile'))
admin_required = role_required(lambda u: u.is_platform_admin)


# --------------------------------------------------------------------------
# Position "live" (simulation de suivi temps réel, sans écriture en base)
# --------------------------------------------------------------------------
def _lerp(a, b, t):
    return a + (b - a) * t


def live_position(mission):
    """Position affichée d'un technicien + minutes restantes estimées.

    Les coordonnées réelles servent de point de départ ; en cours de route, la
    position est interpolée vers le client en fonction du temps écoulé.
    """
    req = mission.request
    base_lat = mission.tech_lat if mission.tech_lat is not None else mission.technician.current_lat
    base_lng = mission.tech_lng if mission.tech_lng is not None else mission.technician.current_lng
    if None in (base_lat, base_lng, req.lat, req.lng):
        return base_lat, base_lng, None
    eta_total = 20.0
    if mission.status == Status.EN_ROUTE and mission.en_route_at:
        elapsed = (timezone.now() - mission.en_route_at).total_seconds() / 60.0
        t = max(0.0, min(1.0, elapsed / eta_total))
        return _lerp(base_lat, req.lat, t), _lerp(base_lng, req.lng, t), max(1, round((1 - t) * eta_total))
    if mission.status in (Status.SUR_SITE, Status.TERMINEE):
        return req.lat, req.lng, 0
    return base_lat, base_lng, round(eta_total)


def _jitter(lat, lng, seed):
    t = timezone.now().timestamp() / 9.0
    return lat + math.sin(t + seed) * 0.0010, lng + math.cos(t + seed * 1.7) * 0.0010


# ==========================================================================
# ESPACE CLIENT
# ==========================================================================
@client_required
def client_dashboard(request):
    reqs = request.user.requests.select_related('skill', 'mission_obj__technician__user')
    active = [r for r in reqs if r.status in ACTIVE_STATUSES or r.status in (Status.SOUMISE, Status.EN_ATTENTE)]
    done = [r for r in reqs if r.status == Status.TERMINEE]
    ctx = {
        'requests': list(reqs)[:6],
        'kpi_total': reqs.count(),
        'kpi_active': len(active),
        'kpi_done': len(done),
        'current': active[0] if active else None,
    }
    return render(request, 'interventions/client/dashboard.html', ctx)


@client_required
def request_create(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.client = request.user
            req.status = Status.SOUMISE
            req.estimated_cost = services.estimate_cost(form.cleaned_data['skill'], req.urgency)
            req.submitted_at = timezone.now()
            req.save()
            for f in request.FILES.getlist('photos')[:5]:
                RequestPhoto.objects.create(request=req, image=f)
            req.log(Status.SOUMISE, actor=request.user, note='Demande soumise')
            ActivityLog.record(request.user, 'Nouvelle demande', req.reference)
            services.auto_assign(req, actor=request.user)
            messages.success(request, "Demande envoyée. Nous recherchons le meilleur technicien proche de vous.")
            return redirect('interventions:request_detail', pk=req.pk)
        messages.error(request, "Veuillez compléter les champs requis.")
    else:
        form = RequestForm()
    return render(request, 'interventions/client/request_form.html',
                  {'form': form, 'estimates': services.BASE_COST,
                   'skills': Skill.objects.all(), 'map_center': None})


@client_required
def request_detail(request, pk):
    req = get_object_or_404(
        InterventionRequest.objects.select_related('skill', 'mission_obj__technician__user'),
        pk=pk, client=request.user)
    mission = getattr(req, 'mission_obj', None)
    idx = req.progress_index
    steps = []
    for i, st in enumerate(TRACKING_STEPS):
        if req.status == Status.TERMINEE:
            state = 'done'
        elif i < idx:
            state = 'done'
        elif i == idx:
            state = 'current'
        else:
            state = ''
        steps.append({'status': st, 'label': Status(st).label, 'state': state})
    review = getattr(mission, 'review', None) if mission else None
    payment = getattr(mission, 'payment', None) if mission else None
    ctx = {
        'req': req, 'mission': mission, 'steps': steps,
        'events': req.events.select_related('actor'),
        'photos': req.photos.all(),
        'review': review, 'payment': payment,
        'can_pay': bool(mission) and req.status == Status.TERMINEE and not payment,
        'can_review': bool(mission) and req.status == Status.TERMINEE and not review,
    }
    return render(request, 'interventions/client/request_detail.html', ctx)


@client_required
@require_POST
def request_cancel(request, pk):
    req = get_object_or_404(InterventionRequest, pk=pk, client=request.user)
    if req.is_cancellable:
        services.cancel_request(req, actor=request.user)
        messages.success(request, "Demande annulée.")
    else:
        messages.error(request, "Cette demande ne peut plus être annulée.")
    return redirect('interventions:request_detail', pk=pk)


@client_required
def request_pay(request, pk):
    req = get_object_or_404(InterventionRequest, pk=pk, client=request.user)
    mission = getattr(req, 'mission_obj', None)
    if not mission or req.status != Status.TERMINEE or hasattr(mission, 'payment'):
        messages.error(request, "Le paiement n'est pas disponible pour cette demande.")
        return redirect('interventions:request_detail', pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            pay = form.save(commit=False)
            pay.mission = mission
            pay.amount = mission.final_cost or req.estimated_cost
            if pay.method == Payment.Method.CASH:
                pay.state = Payment.State.PENDING
                msg = "Paiement en espèces enregistré. Il sera confirmé par l'administration."
            else:
                pay.state = Payment.State.CONFIRMED
                pay.confirmed_at = timezone.now()
                msg = "Paiement confirmé. Merci pour votre confiance."
            pay.save()
            ActivityLog.record(request.user, 'Paiement ' + pay.get_method_display(), req.reference)
            messages.success(request, msg)
            return redirect('interventions:request_detail', pk=pk)
    else:
        form = PaymentForm()
    return render(request, 'interventions/client/pay.html',
                  {'req': req, 'mission': mission, 'form': form,
                   'amount': mission.final_cost or req.estimated_cost})


@client_required
def request_review(request, pk):
    req = get_object_or_404(InterventionRequest, pk=pk, client=request.user)
    mission = getattr(req, 'mission_obj', None)
    if not mission or req.status != Status.TERMINEE or hasattr(mission, 'review'):
        messages.error(request, "L'évaluation n'est pas disponible.")
        return redirect('interventions:request_detail', pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.mission = mission
            review.save()
            services.recompute_rating(mission.technician)
            Notification.push(mission.technician.user, 'Nouvel avis reçu',
                              f'{review.rating}/5 sur {req.reference}.', icon='star')
            messages.success(request, "Merci pour votre évaluation.")
            return redirect('interventions:request_detail', pk=pk)
    else:
        form = ReviewForm()
    return render(request, 'interventions/client/review.html',
                  {'req': req, 'mission': mission, 'form': form})


@client_required
def client_history(request):
    reqs = request.user.requests.select_related('skill', 'mission_obj__technician__user')
    return render(request, 'interventions/client/history.html', {'requests': reqs})


# ==========================================================================
# ESPACE TECHNICIEN
# ==========================================================================
def _tech(request):
    return request.user.technician_profile


@tech_required
def tech_dashboard(request):
    tp = _tech(request)
    missions = tp.missions.select_related('request__skill', 'request__client')
    active = [m for m in missions if m.status in ACTIVE_STATUSES]
    earnings = Payment.objects.filter(
        mission__technician=tp, state=Payment.State.CONFIRMED).aggregate(s=Sum('amount'))['s'] or 0
    available = _available_requests(tp)
    ctx = {
        'tp': tp,
        'current': active[0] if active else None,
        'kpi_active': len(active),
        'kpi_done': tp.completed_missions,
        'kpi_earnings': earnings,
        'kpi_rating': tp.rating_avg,
        'available_count': len(available),
        'recent': list(missions)[:5],
    }
    return render(request, 'interventions/tech/dashboard.html', ctx)


def _available_requests(tp):
    """Demandes en attente qu'un technicien validé peut prendre."""
    if not tp.is_verified:
        return []
    qs = InterventionRequest.objects.filter(
        status__in=[Status.SOUMISE, Status.EN_ATTENTE], mission_obj__isnull=True
    ).select_related('skill', 'client')
    skill_ids = set(tp.skills.values_list('id', flat=True))
    out = []
    for r in qs:
        if skill_ids and r.skill_id and r.skill_id not in skill_ids:
            continue
        r.distance = tp.distance_km(r.lat, r.lng)
        out.append(r)
    out.sort(key=lambda r: r.distance if r.distance is not None else 9999)
    return out


@tech_required
def tech_available(request):
    tp = _tech(request)
    return render(request, 'interventions/tech/available.html',
                  {'tp': tp, 'requests': _available_requests(tp)})


@tech_required
@require_POST
def mission_accept(request, pk):
    tp = _tech(request)
    if not tp.is_verified:
        messages.error(request, "Votre profil doit être validé avant d'accepter des missions.")
        return redirect('interventions:tech_available')
    req = get_object_or_404(InterventionRequest, pk=pk)
    if hasattr(req, 'mission_obj') or req.status not in (Status.SOUMISE, Status.EN_ATTENTE):
        messages.error(request, "Cette demande n'est plus disponible.")
        return redirect('interventions:tech_available')
    mission = Mission.objects.create(
        request=req, technician=tp, status=Status.ACCEPTEE,
        accepted_at=timezone.now(), tech_lat=tp.current_lat, tech_lng=tp.current_lng,
        final_cost=req.estimated_cost)
    tp.availability = TechnicianProfile.Availability.BUSY
    tp.save(update_fields=['availability'])
    req.status = Status.ACCEPTEE
    req.save(update_fields=['status', 'updated_at'])
    req.log(Status.ACCEPTEE, actor=request.user, note='Mission acceptée')
    Notification.push(req.client, 'Technicien affecté',
                      f'{tp.user.display_name} prend en charge {req.reference}.',
                      url=f'/app/client/demande/{req.id}/', icon='check')
    ActivityLog.record(request.user, 'Mission acceptée', req.reference)
    messages.success(request, "Mission acceptée. Bonne intervention.")
    return redirect('interventions:mission_detail', pk=mission.pk)


@tech_required
def mission_detail(request, pk):
    tp = _tech(request)
    mission = get_object_or_404(
        Mission.objects.select_related('request__skill', 'request__client'),
        pk=pk, technician=tp)
    next_status = services.MISSION_FLOW.get(mission.status)
    ctx = {
        'mission': mission, 'req': mission.request,
        'next_status': next_status,
        'next_label': Status(next_status).label if next_status else None,
        'photos': mission.request.photos.all(),
        'events': mission.request.events.all(),
    }
    return render(request, 'interventions/tech/mission_detail.html', ctx)


@tech_required
@require_POST
def mission_advance(request, pk):
    tp = _tech(request)
    mission = get_object_or_404(Mission, pk=pk, technician=tp)
    target = services.MISSION_FLOW.get(mission.status)
    if not target:
        messages.error(request, "Aucune étape suivante disponible.")
        return redirect('interventions:mission_detail', pk=pk)
    if target == Status.TERMINEE:
        cost = request.POST.get('final_cost')
        if cost:
            try:
                mission.final_cost = int(cost)
                mission.save(update_fields=['final_cost'])
            except ValueError:
                pass
    services.advance_mission(mission, target, actor=request.user)
    messages.success(request, f"Statut mis à jour : {Status(target).label}.")
    return redirect('interventions:mission_detail', pk=pk)


@tech_required
@require_POST
def mission_refuse(request, pk):
    tp = _tech(request)
    mission = get_object_or_404(Mission, pk=pk, technician=tp)
    if mission.status != Status.ACCEPTEE:
        messages.error(request, "Une mission déjà démarrée ne peut pas être refusée.")
        return redirect('interventions:mission_detail', pk=pk)
    req = mission.request
    req.status = Status.EN_ATTENTE
    req.save(update_fields=['status', 'updated_at'])
    req.log(Status.EN_ATTENTE, actor=request.user, note='Mission refusée, remise en attente')
    tp.availability = TechnicianProfile.Availability.AVAILABLE
    tp.save(update_fields=['availability'])
    mission.delete()
    ActivityLog.record(request.user, 'Mission refusée', req.reference)
    messages.success(request, "Mission refusée. La demande retourne dans la file.")
    return redirect('interventions:tech_dashboard')


@tech_required
@require_POST
def tech_availability(request):
    tp = _tech(request)
    value = request.POST.get('availability')
    if value in dict(TechnicianProfile.Availability.choices):
        tp.availability = value
        tp.last_seen = timezone.now()
        tp.save(update_fields=['availability', 'last_seen'])
        messages.success(request, "Disponibilité mise à jour.")
    return redirect(request.POST.get('next') or 'interventions:tech_dashboard')


@tech_required
@require_POST
def tech_position_update(request):
    """Partage de position du technicien pendant l'intervention (JSON)."""
    tp = _tech(request)
    try:
        lat = float(request.POST.get('lat'))
        lng = float(request.POST.get('lng'))
    except (TypeError, ValueError):
        return JsonResponse({'ok': False}, status=400)
    tp.current_lat, tp.current_lng, tp.last_seen = lat, lng, timezone.now()
    tp.save(update_fields=['current_lat', 'current_lng', 'last_seen'])
    tp.missions.filter(status__in=ACTIVE_STATUSES).update(tech_lat=lat, tech_lng=lng)
    return JsonResponse({'ok': True})


@tech_required
def tech_documents(request):
    tp = _tech(request)
    if request.method == 'POST':
        form = TechnicianDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.technician = tp
            doc.save()
            ActivityLog.record(request.user, 'Document déposé', doc.get_kind_display())
            messages.success(request, "Document déposé. Il sera examiné par l'administration.")
            return redirect('interventions:tech_documents')
    else:
        form = TechnicianDocumentForm()
    return render(request, 'interventions/tech/documents.html',
                  {'tp': tp, 'form': form, 'documents': tp.documents.all()})


@tech_required
def tech_earnings(request):
    tp = _tech(request)
    payments = Payment.objects.filter(mission__technician=tp).select_related('mission__request')
    total = payments.filter(state=Payment.State.CONFIRMED).aggregate(s=Sum('amount'))['s'] or 0
    pending = payments.filter(state=Payment.State.PENDING).aggregate(s=Sum('amount'))['s'] or 0
    return render(request, 'interventions/tech/earnings.html',
                  {'tp': tp, 'payments': payments, 'total': total, 'pending': pending})


# ==========================================================================
# ESPACE ADMINISTRATION
# ==========================================================================
@admin_required
def admin_dashboard(request):
    reqs = InterventionRequest.objects.all()
    ctx = {
        'kpi_clients': User.objects.filter(role=User.Role.CLIENT).count(),
        'kpi_techs': TechnicianProfile.objects.count(),
        'kpi_requests': reqs.count(),
        'kpi_active': reqs.filter(status__in=ACTIVE_STATUSES).count(),
        'kpi_pending_tech': TechnicianProfile.objects.filter(
            verification=TechnicianProfile.Verification.PENDING).count(),
        'kpi_disputes': Dispute.objects.filter(state=Dispute.State.OPEN).count(),
        'kpi_revenue': Payment.objects.filter(state=Payment.State.CONFIRMED).aggregate(s=Sum('amount'))['s'] or 0,
        'recent_requests': reqs.select_related('client', 'skill')[:8],
        'pending_techs': TechnicianProfile.objects.filter(
            verification=TechnicianProfile.Verification.PENDING).select_related('user')[:5],
        'logs': ActivityLog.objects.select_related('actor')[:10],
    }
    return render(request, 'interventions/admin/dashboard.html', ctx)


@admin_required
def admin_technicians(request):
    techs = TechnicianProfile.objects.select_related('user').prefetch_related('skills', 'documents')
    f = request.GET.get('f')
    if f in dict(TechnicianProfile.Verification.choices):
        techs = techs.filter(verification=f)
    return render(request, 'interventions/admin/technicians.html', {'techs': techs, 'f': f})


@admin_required
@require_POST
def admin_tech_action(request, pk):
    tp = get_object_or_404(TechnicianProfile, pk=pk)
    action = request.POST.get('action')
    if action == 'validate':
        tp.verification = TechnicianProfile.Verification.VERIFIED
        tp.availability = TechnicianProfile.Availability.AVAILABLE
        tp.documents.update(status='validated')
        Notification.push(tp.user, 'Profil validé', 'Vous pouvez désormais recevoir des missions.', icon='check')
        messages.success(request, f"{tp.user.display_name} est validé.")
    elif action == 'reject':
        tp.verification = TechnicianProfile.Verification.REJECTED
        Notification.push(tp.user, 'Profil rejeté', "Contactez l'administration pour en savoir plus.", icon='x-circle')
        messages.success(request, f"{tp.user.display_name} a été rejeté.")
    tp.save()
    ActivityLog.record(request.user, 'Validation technicien : ' + (action or ''), tp.user.display_name)
    return redirect('interventions:admin_technicians')


@admin_required
def admin_requests(request):
    reqs = InterventionRequest.objects.select_related('client', 'skill', 'mission_obj__technician__user')
    f = request.GET.get('f')
    if f in dict(Status.choices):
        reqs = reqs.filter(status=f)
    return render(request, 'interventions/admin/requests.html',
                  {'requests': reqs, 'f': f, 'statuses': Status.choices})


@admin_required
@require_POST
def admin_assign(request, pk):
    req = get_object_or_404(InterventionRequest, pk=pk)
    if hasattr(req, 'mission_obj'):
        messages.error(request, "Cette demande a déjà une mission.")
    else:
        mission = services.auto_assign(req, actor=request.user)
        if mission:
            messages.success(request, f"Affecté à {mission.technician.user.display_name}.")
        else:
            messages.error(request, "Aucun technicien disponible pour cette demande.")
    return redirect('interventions:admin_requests')


@admin_required
def admin_map(request):
    return render(request, 'interventions/admin/map.html', {})


@admin_required
def admin_payments(request):
    payments = Payment.objects.select_related('mission__request__client', 'mission__technician__user')
    return render(request, 'interventions/admin/payments.html', {'payments': payments})


@admin_required
@require_POST
def admin_payment_confirm(request, pk):
    pay = get_object_or_404(Payment, pk=pk)
    pay.state = Payment.State.CONFIRMED
    pay.confirmed_by = request.user
    pay.confirmed_at = timezone.now()
    pay.save()
    Notification.push(pay.mission.request.client, 'Paiement confirmé',
                      f'{pay.mission.request.reference}.', icon='check')
    ActivityLog.record(request.user, 'Paiement confirmé', pay.reference)
    messages.success(request, "Paiement confirmé.")
    return redirect('interventions:admin_payments')


@admin_required
def admin_disputes(request):
    disputes = Dispute.objects.select_related('mission__request', 'opened_by')
    return render(request, 'interventions/admin/disputes.html', {'disputes': disputes})


@admin_required
@require_POST
def admin_dispute_action(request, pk):
    d = get_object_or_404(Dispute, pk=pk)
    action = request.POST.get('action')
    d.resolution = request.POST.get('resolution', '')
    if action == 'resolve':
        d.state = Dispute.State.RESOLVED
    elif action == 'reject':
        d.state = Dispute.State.REJECTED
    d.resolved_at = timezone.now()
    d.save()
    ActivityLog.record(request.user, 'Litige traité : ' + (action or ''), d.mission.request.reference)
    messages.success(request, "Litige mis à jour.")
    return redirect('interventions:admin_disputes')


@admin_required
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
    role = request.GET.get('role')
    if role in dict(User.Role.choices):
        users = users.filter(role=role)
    return render(request, 'interventions/admin/users.html', {'users': users, 'role': role})


@admin_required
@require_POST
def admin_user_toggle(request, pk):
    u = get_object_or_404(User, pk=pk)
    if u.is_superuser:
        messages.error(request, "Impossible de suspendre un super-administrateur.")
    else:
        u.is_suspended = not u.is_suspended
        u.is_active = not u.is_suspended
        u.save(update_fields=['is_suspended', 'is_active'])
        ActivityLog.record(request.user, 'Compte ' + ('suspendu' if u.is_suspended else 'réactivé'), u.display_name)
        messages.success(request, "Compte suspendu." if u.is_suspended else "Compte réactivé.")
    return redirect('interventions:admin_users')


# ==========================================================================
# NOTIFICATIONS (commun)
# ==========================================================================
@login_required
def notifications(request):
    notifs = request.user.notifications.all()
    if request.method == 'POST':
        notifs.update(is_read=True)
        return redirect('interventions:notifications')
    return render(request, 'interventions/notifications.html', {'notifs': notifs})


# ==========================================================================
# API JSON — cartes temps réel
# ==========================================================================
@admin_required
def positions_api(request):
    """Positions des techniciens et interventions actives, pour la carte admin."""
    techs = []
    for tp in TechnicianProfile.objects.select_related('user').filter(
            verification=TechnicianProfile.Verification.VERIFIED):
        if tp.current_lat is None:
            continue
        active = tp.missions.filter(status__in=ACTIVE_STATUSES).first()
        if active:
            lat, lng, eta = live_position(active)
            ref = active.request.reference
        else:
            lat, lng = _jitter(tp.current_lat, tp.current_lng, tp.id)
            ref, eta = None, None
        techs.append({
            'id': tp.id, 'name': tp.user.display_name,
            'lat': round(lat, 6), 'lng': round(lng, 6),
            'status': tp.availability, 'rating': tp.rating_avg,
            'mission': ref, 'eta': eta,
        })
    interventions = []
    for r in InterventionRequest.objects.filter(status__in=ACTIVE_STATUSES).select_related('client'):
        if r.lat is None:
            continue
        interventions.append({
            'ref': r.reference, 'lat': r.lat, 'lng': r.lng,
            'client': r.client.display_name, 'status': r.get_status_display(),
            'tone': r.tone,
        })
    return JsonResponse({'technicians': techs, 'interventions': interventions,
                         'updated': timezone.now().strftime('%H:%M:%S')})


@client_required
def mission_position_api(request, pk):
    """Position live du technicien pour le suivi client d'une demande."""
    req = get_object_or_404(InterventionRequest, pk=pk, client=request.user)
    mission = getattr(req, 'mission_obj', None)
    if not mission:
        return JsonResponse({'ok': False})
    lat, lng, eta = live_position(mission)
    return JsonResponse({
        'ok': True, 'status': mission.status, 'status_label': mission.get_status_display(),
        'tech': mission.technician.user.display_name,
        'tech_lat': lat, 'tech_lng': lng, 'eta': eta,
        'client_lat': req.lat, 'client_lng': req.lng,
    })
