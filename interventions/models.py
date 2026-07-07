"""Cœur métier : demandes d'intervention, missions, paiements, avis, litiges.

Le cycle de vie d'une demande suit les statuts imposés par le cahier des
charges : Brouillon, Soumise, En attente, Acceptée, En route, Sur site,
Terminée, Annulée, Litige. Chaque changement de statut est historisé.
"""
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import Skill, TechnicianProfile


class Status(models.TextChoices):
    BROUILLON = 'brouillon', 'Brouillon'
    SOUMISE = 'soumise', 'Soumise'
    EN_ATTENTE = 'en_attente', 'En attente'
    ACCEPTEE = 'acceptee', 'Acceptée'
    EN_ROUTE = 'en_route', 'En route'
    SUR_SITE = 'sur_site', 'Sur site'
    TERMINEE = 'terminee', 'Terminée'
    ANNULEE = 'annulee', 'Annulée'
    LITIGE = 'litige', 'Litige'


# Couleur du badge associée à chaque statut (classe CSS du design system)
STATUS_TONE = {
    Status.BROUILLON: 'muted',
    Status.SOUMISE: 'info',
    Status.EN_ATTENTE: 'info',
    Status.ACCEPTEE: 'accent',
    Status.EN_ROUTE: 'accent',
    Status.SUR_SITE: 'accent',
    Status.TERMINEE: 'success',
    Status.ANNULEE: 'muted',
    Status.LITIGE: 'danger',
}

# Étapes de progression montrées au client dans le suivi temps réel
TRACKING_STEPS = [
    Status.SOUMISE, Status.ACCEPTEE, Status.EN_ROUTE, Status.SUR_SITE, Status.TERMINEE,
]

ACTIVE_STATUSES = [
    Status.ACCEPTEE, Status.EN_ROUTE, Status.SUR_SITE,
]


def make_reference():
    return 'TILE-' + secrets.token_hex(3).upper()


class Urgency(models.TextChoices):
    LOW = 'faible', 'Faible'
    NORMAL = 'normale', 'Normale'
    HIGH = 'haute', 'Haute'
    CRITICAL = 'urgente', 'Urgente'


class InterventionRequest(models.Model):
    reference = models.CharField(max_length=16, unique=True, default=make_reference, editable=False)
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='requests')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='requests', verbose_name='Type de service')
    title = models.CharField('Titre', max_length=120)
    description = models.TextField('Description du problème')
    urgency = models.CharField(max_length=10, choices=Urgency.choices, default=Urgency.NORMAL)
    address = models.CharField('Adresse', max_length=200, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    estimated_cost = models.PositiveIntegerField('Estimation (FCFA)', default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.BROUILLON)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Demande d'intervention"
        verbose_name_plural = "Demandes d'intervention"

    def __str__(self):
        return f'{self.reference} · {self.title}'

    # --- helpers d'affichage ---
    @property
    def tone(self):
        return STATUS_TONE.get(self.status, 'muted')

    @property
    def is_active(self):
        return self.status in ACTIVE_STATUSES

    @property
    def is_cancellable(self):
        # Le client peut annuler avant l'acceptation d'un technicien.
        return self.status in (Status.SOUMISE, Status.EN_ATTENTE)

    @property
    def mission(self):
        return getattr(self, 'mission_obj', None)

    @property
    def progress_index(self):
        order = {s: i for i, s in enumerate(TRACKING_STEPS)}
        if self.status == Status.TERMINEE:
            return len(TRACKING_STEPS) - 1
        return order.get(self.status, 0)

    def log(self, status, actor=None, note=''):
        StatusEvent.objects.create(request=self, status=status, actor=actor, note=note)


class RequestPhoto(models.Model):
    request = models.ForeignKey(InterventionRequest, on_delete=models.CASCADE,
                                related_name='photos')
    image = models.ImageField(upload_to='requests/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Photo · {self.request.reference}'


class Mission(models.Model):
    request = models.OneToOneField(InterventionRequest, on_delete=models.CASCADE,
                                   related_name='mission_obj')
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE,
                                   related_name='missions')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACCEPTEE)
    accepted_at = models.DateTimeField(null=True, blank=True)
    en_route_at = models.DateTimeField(null=True, blank=True)
    on_site_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    # Position live du technicien pendant la mission (suivi temps réel)
    tech_lat = models.FloatField(null=True, blank=True)
    tech_lng = models.FloatField(null=True, blank=True)
    final_cost = models.PositiveIntegerField('Montant final (FCFA)', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Mission {self.request.reference} · {self.technician.user.display_name}'

    @property
    def tone(self):
        return STATUS_TONE.get(self.status, 'muted')


class StatusEvent(models.Model):
    """Historisation de chaque changement de statut d'une demande."""
    request = models.ForeignKey(InterventionRequest, on_delete=models.CASCADE,
                                related_name='events')
    status = models.CharField(max_length=12, choices=Status.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                              null=True, blank=True)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.request.reference} → {self.get_status_display()}'

    @property
    def tone(self):
        return STATUS_TONE.get(self.status, 'muted')


class Payment(models.Model):
    class Method(models.TextChoices):
        ORANGE = 'orange_money', 'Orange Money'
        MOOV = 'moov', 'Moov Money'
        CASH = 'cash', 'Espèces'

    class State(models.TextChoices):
        PENDING = 'pending', 'En attente'
        CONFIRMED = 'confirmed', 'Confirmé'
        FAILED = 'failed', 'Échec'

    mission = models.OneToOneField(Mission, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=14, choices=Method.choices, default=Method.ORANGE)
    amount = models.PositiveIntegerField('Montant (FCFA)')
    state = models.CharField(max_length=10, choices=State.choices, default=State.PENDING)
    reference = models.CharField(max_length=24, default=make_reference, editable=False)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='confirmed_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Paiement {self.amount} FCFA · {self.get_method_display()}'

    @property
    def tone(self):
        return {'pending': 'info', 'confirmed': 'success', 'failed': 'danger'}.get(self.state, 'muted')


class Review(models.Model):
    mission = models.OneToOneField(Mission, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveSmallIntegerField('Note', default=5)
    comment = models.TextField('Commentaire', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Avis {self.rating}/5 · {self.mission.request.reference}'

    @property
    def star_range(self):
        return range(self.rating)

    @property
    def empty_range(self):
        return range(5 - self.rating)


class Dispute(models.Model):
    class State(models.TextChoices):
        OPEN = 'open', 'Ouvert'
        RESOLVED = 'resolved', 'Résolu'
        REJECTED = 'rejected', 'Rejeté'

    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name='disputes')
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, related_name='disputes')
    reason = models.TextField('Motif')
    state = models.CharField(max_length=10, choices=State.choices, default=State.OPEN)
    resolution = models.TextField('Résolution', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Litige · {self.mission.request.reference}'

    @property
    def tone(self):
        return {'open': 'danger', 'resolved': 'success', 'rejected': 'muted'}.get(self.state, 'muted')


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='notifications')
    title = models.CharField(max_length=140)
    body = models.CharField(max_length=240, blank=True)
    url = models.CharField(max_length=240, blank=True)
    icon = models.CharField(max_length=40, default='bell')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Notif · {self.user.display_name} · {self.title}'

    @staticmethod
    def push(user, title, body='', url='', icon='bell'):
        return Notification.objects.create(user=user, title=title, body=body, url=url, icon=icon)


class ContactLead(models.Model):
    """Prospect recueilli via le formulaire de contact de la landing page."""
    name = models.CharField('Nom', max_length=120)
    email = models.EmailField()
    phone = models.CharField('Téléphone', max_length=30, blank=True)
    subject = models.CharField('Sujet', max_length=140, blank=True)
    message = models.TextField('Message')
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField('Traité', default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prospect'

    def __str__(self):
        return f'{self.name} · {self.email}'


class ActivityLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='actions')
    verb = models.CharField(max_length=160)
    target = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Journal d'activité"
        verbose_name_plural = "Journal d'activité"

    def __str__(self):
        return f'{self.actor} · {self.verb}'

    @staticmethod
    def record(actor, verb, target=''):
        return ActivityLog.objects.create(actor=actor, verb=verb, target=target)
