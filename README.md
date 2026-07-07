# TILE ÉNERGIE

Plateforme de mise en relation entre clients et techniciens solaires qualifiés
(installation, maintenance et dépannage), pour le Mali. Le projet couvre la
landing page de présentation et l'application web complète, entièrement en
Django avec une base SQLite.

## Démarrer

```bash
pip install -r requirements.txt
python manage.py migrate      # la base SQLite existe déjà
python manage.py seed         # données de démonstration (idempotent)
python manage.py runserver
```

Puis ouvrir http://127.0.0.1:8000/

Dépendances : Django et Pillow (voir `requirements.txt`). Leaflet est **hébergé en
local** dans `static/vendor/leaflet/`, donc les cartes fonctionnent sans CDN ;
seules les tuiles OpenStreetMap nécessitent une connexion Internet.

## Comptes de démonstration

| Rôle | Identifiant (email) | Mot de passe |
|------|---------------------|--------------|
| Administration | `admin@tile-energie.ml` | `tileadmin` |
| Client | `client@demo.ml` | `demo1234` |
| Technicien (validé) | `moussa@demo.ml` | `demo1234` |
| Technicien (à valider) | `sekou@demo.ml` | `demo1234` |

La connexion se fait avec l'email. L'admin Django reste disponible sur `/admin/`.

## Ce que contient le projet

**Landing page** : hero avec carrousel de photos réelles, bandeau défilant,
problème/solution, services, galerie qui défile, parcours en 4 étapes, chiffres
animés, avantages, témoignages, FAQ, appels à l'action, et l'assistant Tila
(chatbot à choix multiples servi par Django).

**Pages publiques** : présentation du service, calculateur de dimensionnement
solaire (panneaux, batteries, onduleur, budget, calcul instantané), FAQ, contact
avec carte de localisation (Leaflet + OpenStreetMap).

**Espace client** : tableau de bord, création de demande (description, photos,
position sur carte, estimation), suivi en temps réel du technicien sur une carte,
historique, paiement (Orange Money, Moov, espèces), évaluation.

**Espace technicien** : tableau de bord, disponibilité, demandes disponibles,
acceptation/refus, avancement des statuts, partage de position, documents, gains.

**Espace administration** : tableau de bord, **carte des interventions en temps
réel** (positions des techniciens actualisées en direct), gestion des demandes
et affectation, validation des techniciens, paiements, litiges, utilisateurs,
journal d'activité.

## Architecture

- `accounts/` : modèle `User` personnalisé (rôles client / technicien / admin),
  profils, compétences, documents, authentification.
- `interventions/` : demandes, missions, statuts historisés, paiements, avis,
  litiges, notifications, journal, services métier et API JSON temps réel.
- `website/` : pages publiques, calculateur, contact, assistant, design system.
- `templates/`, `static/` : design system maison (palette du logo, aucune
  dépendance CSS lourde).

## Choix de conception

- Couleurs issues du logo : navy `#03234E`, orange solaire `#F77818`, jaune.
- Aucun dégradé, aucune police Inter (Space Grotesk + DM Sans), aucune emoji
  (jeu d'icônes SVG maison), pas de tiret cadratin dans les textes.
- Responsive soigné sur mobile.
- Cartes : Leaflet (hébergé en local) + tuiles OpenStreetMap, aucune clé d'API.

## Note sur le temps réel

Les positions affichées sur les cartes sont calculées côté serveur à partir des
positions réelles enregistrées : un technicien en route est interpolé vers le
client selon le temps écoulé, et les techniciens disponibles dérivent légèrement.
Le suivi est donc une simulation fidèle, sans service de géolocalisation externe.
