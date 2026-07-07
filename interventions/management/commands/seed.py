"""Jeu de données de démonstration pour TILE ÉNERGIE.

Crée un administrateur, un client, plusieurs techniciens géolocalisés autour de
Bamako et des demandes couvrant tous les statuts, avec missions, avis,
paiements et un litige, afin que les tableaux de bord et la carte temps réel
soient peuplés immédiatement.

    python manage.py seed
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import (ClientProfile, Skill, TechnicianDocument,
                             TechnicianProfile, User)
from interventions.models import (ActivityLog, Dispute, InterventionRequest,
                                  Mission, Notification, Payment, Review,
                                  Status, StatusEvent, Urgency)
from interventions import services
from website import content


TECHS = [
    # nom, email, skills(slugs), zone, lat, lng, rating, count, done, dispo, verif
    ("Moussa Keïta", "moussa@demo.ml", ['installation-panneaux', 'diagnostic-pannes'], "Hamdallaye, Bamako", 12.6300, -8.0200, 4.8, 36, 36, 'available', 'verified'),
    ("Oumar Traoré", "oumar@demo.ml", ['reparation-batteries', 'maintenance-onduleurs'], "ACI 2000, Bamako", 12.6450, -8.0400, 4.9, 52, 52, 'available', 'verified'),
    ("Awa Sangaré", "awa.tech@demo.ml", ['maintenance-onduleurs', 'conseil-optimisation'], "Badalabougou, Bamako", 12.6180, -7.9900, 4.6, 21, 21, 'busy', 'verified'),
    ("Ibrahim Cissé", "ibrahim@demo.ml", ['installation-panneaux', 'reparation-batteries'], "Kalaban Coura, Bamako", 12.5900, -7.9800, 4.7, 28, 28, 'available', 'verified'),
    ("Fatou Coulibaly", "fatou.tech@demo.ml", ['diagnostic-pannes', 'maintenance-onduleurs'], "Magnambougou, Bamako", 12.6000, -7.9500, 4.5, 14, 14, 'available', 'verified'),
    ("Sékou Diallo", "sekou@demo.ml", ['installation-panneaux'], "Kati", 12.7440, -8.0730, 0.0, 0, 0, 'offline', 'pending'),
]

# Demandes : titre, skill, urgence, adresse, lat, lng, statut, technicien(index ou None), avis(0-5), paiement('cash'|'orange'|None), litige(bool)
REQUESTS = [
    ("Plus de courant depuis ce matin", 'diagnostic-pannes', Urgency.HIGH, "Hamdallaye ACI, près du marché", 12.6320, -8.0180, Status.EN_ROUTE, 0, None, None, False),
    ("Batterie qui ne tient plus la charge", 'reparation-batteries', Urgency.NORMAL, "ACI 2000, rue 390", 12.6470, -8.0380, Status.SUR_SITE, 1, None, None, False),
    ("Installation de 6 panneaux sur toiture", 'installation-panneaux', Urgency.NORMAL, "Badalabougou Est", 12.6160, -7.9920, Status.ACCEPTEE, 2, None, None, False),
    ("Onduleur qui bipe sans arrêt", 'maintenance-onduleurs', Urgency.HIGH, "Magnambougou Faso Kanu", 12.6010, -7.9520, Status.TERMINEE, 4, 5, 'orange', False),
    ("Nettoyage et contrôle des panneaux", 'conseil-optimisation', Urgency.LOW, "Sotuba ACI", 12.6600, -7.9500, Status.TERMINEE, 1, 4, 'cash', False),
    ("Coupure intermittente le soir", 'diagnostic-pannes', Urgency.NORMAL, "Kalaban Coura, rue 200", 12.5910, -7.9810, Status.EN_ATTENTE, None, None, None, False),
    ("Remplacement régulateur défectueux", 'maintenance-onduleurs', Urgency.NORMAL, "Djicoroni Para", 12.6450, -8.0300, Status.SOUMISE, None, None, None, False),
    ("Devis pour extension solaire", 'installation-panneaux', Urgency.LOW, "Faladié SEMA", 12.5980, -7.9600, Status.ANNULEE, None, None, None, False),
    ("Litige sur intervention batteries", 'reparation-batteries', Urgency.NORMAL, "Sebenikoro", 12.6300, -8.0600, Status.TERMINEE, 3, None, 'cash', True),
]


class Command(BaseCommand):
    help = "Crée un jeu de données de démonstration pour TILE ÉNERGIE."

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write("Création des compétences...")
        skills = {}
        for s in content.SKILLS:
            obj, _ = Skill.objects.get_or_create(
                slug=s['slug'],
                defaults={'name': s['name'], 'description': s['description'], 'icon': s['icon']})
            skills[s['slug']] = obj

        # --- Administrateur ---
        admin_email = "admin@tile-energie.ml"
        if not User.objects.filter(username=admin_email).exists():
            admin = User.objects.create_superuser(
                username=admin_email, email=admin_email, password="tileadmin",
                first_name="Admin", last_name="TILE")
            admin.role = User.Role.ADMIN
            admin.phone = "+223 76 00 00 00"
            admin.save()
        else:
            admin = User.objects.get(username=admin_email)

        # --- Client de démonstration ---
        client = self._user("client@demo.ml", "Awa", "Diarra", User.Role.CLIENT,
                            phone="+223 70 11 22 33", city="Bamako")
        ClientProfile.objects.get_or_create(
            user=client, defaults={'address': "Hamdallaye ACI 2000", 'installation_note': "4 panneaux, 2 batteries"})

        # --- Techniciens ---
        self.stdout.write("Création des techniciens...")
        tech_objs = []
        for (name, email, sk, zone, lat, lng, rating, count, done, dispo, verif) in TECHS:
            first, last = name.split(' ', 1)
            u = self._user(email, first, last, User.Role.TECHNICIEN, phone="+223 65 00 00 0" + str(len(tech_objs)))
            tp, _ = TechnicianProfile.objects.get_or_create(user=u)
            tp.zones = zone
            tp.current_lat, tp.current_lng = lat, lng
            tp.last_seen = now
            tp.rating_avg, tp.rating_count, tp.completed_missions = rating, count, done
            tp.experience_years = 3 + len(tech_objs)
            tp.availability = dispo
            tp.verification = verif
            tp.bio = f"Technicien solaire expérimenté, spécialisé dans {zone.split(',')[0]}."
            tp.hourly_indication = 5000 + 500 * len(tech_objs)
            tp.save()
            tp.skills.set([skills[s] for s in sk])
            if verif == 'verified':
                TechnicianDocument.objects.get_or_create(
                    technician=tp, kind=TechnicianDocument.Kind.ID,
                    defaults={'file': 'documents/demo-id.txt', 'status': 'validated'})
            tech_objs.append(tp)

        # --- Demandes ---
        if client.requests.exists():
            self.stdout.write(self.style.WARNING("Le client a déjà des demandes, création ignorée."))
        else:
            self.stdout.write("Création des demandes et missions...")
            for i, (title, sk, urg, addr, lat, lng, status, tech_idx, stars, pay, litige) in enumerate(REQUESTS):
                skill = skills[sk]
                created = now - timedelta(days=i, hours=2)
                req = InterventionRequest.objects.create(
                    client=client, skill=skill, title=title,
                    description=f"{title}. Détails fournis par le client lors de la demande, intervention à {addr}.",
                    urgency=urg, address=addr, lat=lat, lng=lng,
                    estimated_cost=services.estimate_cost(skill, urg), status=status,
                    submitted_at=created)
                InterventionRequest.objects.filter(pk=req.pk).update(created_at=created)
                StatusEvent.objects.create(request=req, status=Status.SOUMISE, actor=client,
                                           note="Demande soumise")

                if tech_idx is not None and status != Status.ANNULEE:
                    tp = tech_objs[tech_idx]
                    mission = Mission.objects.create(
                        request=req, technician=tp, status=status,
                        accepted_at=created + timedelta(minutes=4),
                        tech_lat=tp.current_lat, tech_lng=tp.current_lng,
                        final_cost=req.estimated_cost)
                    StatusEvent.objects.create(request=req, status=Status.ACCEPTEE, actor=tp.user,
                                               note=f"Affecté à {tp.user.display_name}")
                    if status in (Status.EN_ROUTE, Status.SUR_SITE, Status.TERMINEE):
                        mission.en_route_at = now - timedelta(minutes=6)
                        StatusEvent.objects.create(request=req, status=Status.EN_ROUTE, actor=tp.user)
                    if status in (Status.SUR_SITE, Status.TERMINEE):
                        mission.on_site_at = now - timedelta(minutes=3)
                        StatusEvent.objects.create(request=req, status=Status.SUR_SITE, actor=tp.user)
                    if status == Status.TERMINEE:
                        mission.completed_at = now - timedelta(minutes=1)
                        StatusEvent.objects.create(request=req, status=Status.TERMINEE, actor=tp.user)
                    mission.save()

                    if pay:
                        method = Payment.Method.ORANGE if pay == 'orange' else Payment.Method.CASH
                        state = Payment.State.CONFIRMED if pay == 'orange' else (
                            Payment.State.PENDING if litige else Payment.State.CONFIRMED)
                        Payment.objects.create(
                            mission=mission, method=method, amount=mission.final_cost,
                            state=state, confirmed_by=(admin if state == Payment.State.CONFIRMED else None),
                            confirmed_at=(now if state == Payment.State.CONFIRMED else None))
                    if stars:
                        Review.objects.create(mission=mission, rating=stars,
                                              comment="Intervention rapide et soignée, je recommande." if stars >= 5 else "Travail correct, technicien ponctuel.")
                    if litige:
                        Dispute.objects.create(mission=mission, opened_by=client,
                                               reason="La panne est réapparue deux jours après l'intervention.",
                                               state=Dispute.State.OPEN)
                        req.status = Status.LITIGE
                        req.save(update_fields=['status'])

            Notification.push(client, "Bienvenue sur TILE ÉNERGIE",
                              "Votre espace client est prêt. Suivez vos demandes en temps réel.", icon='sun')
            Notification.push(tech_objs[0].user, "Nouvelle mission",
                              "Une intervention vous a été affectée.", icon='bolt')
            ActivityLog.record(admin, "Initialisation des données de démonstration", "seed")

        self.stdout.write(self.style.SUCCESS("\nDonnées de démonstration prêtes."))
        self.stdout.write("Comptes de test (mot de passe entre parenthèses) :")
        self.stdout.write("  Admin      : admin@tile-energie.ml (tileadmin)")
        self.stdout.write("  Client     : client@demo.ml (demo1234)")
        self.stdout.write("  Technicien : moussa@demo.ml (demo1234)")
        self.stdout.write("  Technicien (à valider) : sekou@demo.ml (demo1234)")

    def _user(self, email, first, last, role, phone="", city="Bamako"):
        u, created = User.objects.get_or_create(
            username=email,
            defaults={'email': email, 'first_name': first, 'last_name': last,
                      'role': role, 'phone': phone, 'city': city})
        if created:
            u.set_password("demo1234")
            u.save()
        return u
