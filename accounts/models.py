"""Comptes et profils de la plateforme TILE ÉNERGIE.

Trois rôles : client, technicien et administrateur. Le modèle ``User`` étend
``AbstractUser`` afin de porter le rôle directement sur le compte, ce qui
simplifie le contrôle d'accès dans tout le projet.
"""
import math

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = 'client', 'Client'
        TECHNICIEN = 'technicien', 'Technicien'
        ADMIN = 'admin', 'Administrateur'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    phone = models.CharField('Téléphone', max_length=30, blank=True)
    city = models.CharField('Ville', max_length=80, blank=True, default='Bamako')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_suspended = models.BooleanField('Compte suspendu', default=False)

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_technicien(self):
        return self.role == self.Role.TECHNICIEN

    @property
    def is_platform_admin(self):
        return self.role == self.Role.ADMIN or self.is_staff or self.is_superuser

    @property
    def display_name(self):
        full = self.get_full_name().strip()
        return full or self.username

    @property
    def initials(self):
        parts = (self.get_full_name() or self.username).split()
        if len(parts) >= 2:
            return (parts[0][:1] + parts[1][:1]).upper()
        return self.username[:2].upper()

    def __str__(self):
        return f'{self.display_name} ({self.get_role_display()})'


class Skill(models.Model):
    """Domaine de compétence d'un technicien (cf. cahier des charges)."""
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=40, default='wrench', help_text="Identifiant de l'icône SVG")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ClientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='client_profile')
    address = models.CharField('Adresse', max_length=200, blank=True)
    default_lat = models.FloatField(null=True, blank=True)
    default_lng = models.FloatField(null=True, blank=True)
    installation_note = models.CharField("Type d'installation", max_length=200, blank=True)

    def __str__(self):
        return f'Profil client · {self.user.display_name}'


class TechnicianProfile(models.Model):
    class Availability(models.TextChoices):
        AVAILABLE = 'available', 'Disponible'
        BUSY = 'busy', 'En intervention'
        OFFLINE = 'offline', 'Hors ligne'

    class Verification(models.TextChoices):
        PENDING = 'pending', 'En attente de validation'
        VERIFIED = 'verified', 'Validé'
        REJECTED = 'rejected', 'Rejeté'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='technician_profile')
    bio = models.TextField('Présentation', blank=True)
    skills = models.ManyToManyField(Skill, related_name='technicians', blank=True)
    zones = models.CharField("Zones d'intervention", max_length=200, blank=True)
    experience_years = models.PositiveIntegerField("Années d'expérience", default=0)
    verification = models.CharField(max_length=12, choices=Verification.choices,
                                    default=Verification.PENDING)
    availability = models.CharField(max_length=12, choices=Availability.choices,
                                    default=Availability.OFFLINE)
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    rating_avg = models.FloatField('Note moyenne', default=0)
    rating_count = models.PositiveIntegerField(default=0)
    completed_missions = models.PositiveIntegerField('Missions terminées', default=0)
    hourly_indication = models.PositiveIntegerField('Indication FCFA / heure', default=5000)

    class Meta:
        ordering = ['-rating_avg', '-completed_missions']

    @property
    def is_verified(self):
        return self.verification == self.Verification.VERIFIED

    @property
    def is_available(self):
        return self.availability == self.Availability.AVAILABLE

    @property
    def stars(self):
        """Liste pour afficher 5 étoiles : 'full' / 'half' / 'empty'."""
        out, val = [], self.rating_avg
        for i in range(1, 6):
            if val >= i:
                out.append('full')
            elif val >= i - 0.5:
                out.append('half')
            else:
                out.append('empty')
        return out

    def distance_km(self, lat, lng):
        """Distance haversine vers un point (km), ou None si position inconnue."""
        if None in (self.current_lat, self.current_lng, lat, lng):
            return None
        r = 6371.0
        d_lat = math.radians(lat - self.current_lat)
        d_lng = math.radians(lng - self.current_lng)
        a = (math.sin(d_lat / 2) ** 2
             + math.cos(math.radians(self.current_lat)) * math.cos(math.radians(lat))
             * math.sin(d_lng / 2) ** 2)
        return round(r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)

    def __str__(self):
        return f'Technicien · {self.user.display_name}'


class TechnicianDocument(models.Model):
    class Kind(models.TextChoices):
        ID = 'id', "Pièce d'identité"
        CERT = 'cert', 'Certification / diplôme'
        OTHER = 'other', 'Autre justificatif'

    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        VALIDATED = 'validated', 'Validé'
        REJECTED = 'rejected', 'Rejeté'

    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE,
                                   related_name='documents')
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.ID)
    file = models.FileField(upload_to='documents/')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.get_kind_display()} · {self.technician.user.display_name}'
