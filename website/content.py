"""Contenu éditorial de référence (services, chiffres, avis, FAQ).

Source unique réutilisée par les vues publiques et par la commande de seed,
pour que le site ait toujours du contenu cohérent.
"""

SKILLS = [
    {'slug': 'installation-panneaux', 'name': 'Installation de panneaux', 'icon': 'panel',
     'description': "Pose, orientation et raccordement de panneaux solaires, du foyer au site professionnel."},
    {'slug': 'reparation-batteries', 'name': 'Réparation de batteries', 'icon': 'battery',
     'description': "Diagnostic, entretien et remplacement de vos parcs de batteries."},
    {'slug': 'maintenance-onduleurs', 'name': 'Onduleurs et régulateurs', 'icon': 'plug',
     'description': "Maintenance des onduleurs et régulateurs pour une énergie stable au quotidien."},
    {'slug': 'diagnostic-pannes', 'name': 'Diagnostic de pannes', 'icon': 'gauge',
     'description': "Identification rapide de l'origine d'une panne, sur place et en sécurité."},
    {'slug': 'conseil-optimisation', 'name': 'Conseil et optimisation', 'icon': 'leaf',
     'description': "Optimisation de votre consommation et de votre production d'énergie solaire."},
]

OBJECTIFS = [
    {'icon': 'route', 'title': "Faciliter l'accès",
     'text': "Mettre un technicien solaire qualifié à portée de clic, partout dans la zone."},
    {'icon': 'clock', 'title': "Réduire les délais",
     'text': "Diminuer le temps de traitement des demandes d'intervention."},
    {'icon': 'users', 'title': "Créer de l'emploi",
     'text': "Offrir des opportunités concrètes aux jeunes techniciens."},
    {'icon': 'shield', 'title': "Garantir la qualité",
     'text': "Améliorer la fiabilité des installations et des réparations."},
    {'icon': 'leaf', 'title': "Promouvoir le solaire",
     'text': "Encourager l'usage des énergies renouvelables au quotidien."},
    {'icon': 'handshake', 'title': "Créer la confiance",
     'text': "Structurer la relation entre clients et techniciens."},
]

# Étapes du parcours client
STEPS = [
    {'icon': 'chat', 'title': 'Décrivez la panne',
     'text': "Quelques mots, votre position et au besoin une photo. La demande part en moins d'une minute."},
    {'icon': 'route', 'title': 'Un technicien est affecté',
     'text': "La plateforme choisit le professionnel qualifié le plus proche et disponible."},
    {'icon': 'navigation', 'title': 'Suivez en temps réel',
     'text': "Vous voyez le technicien se rapprocher et l'heure d'arrivée estimée."},
    {'icon': 'check-circle', 'title': 'Payez et notez',
     'text': "Réglez par Orange Money, Moov ou en espèces, puis évaluez l'intervention."},
]

STATS = [
    {'count': '320', 'suffix': '+', 'label': 'Interventions réalisées'},
    {'count': '48', 'suffix': '', 'label': 'Techniciens du réseau'},
    {'count': '35', 'suffix': ' min', 'label': "Délai moyen d'arrivée"},
    {'count': '4.8', 'suffix': '/5', 'label': 'Satisfaction client'},
]

# Avantages par public
ADVANTAGES = {
    'client': [
        {'icon': 'clock', 'title': "Gain de temps", 'text': "Un professionnel près de chez vous en quelques clics."},
        {'icon': 'shield', 'title': "Techniciens vérifiés", 'text': "Profils validés et notés par la communauté."},
        {'icon': 'coins', 'title': "Transparence", 'text': "Une estimation claire avant chaque intervention."},
    ],
    'tech': [
        {'icon': 'bolt', 'title': "Plus de missions", 'text': "Recevez des demandes qualifiées dans votre zone."},
        {'icon': 'trending', 'title': "Revenus en hausse", 'text': "Développez votre activité sans démarchage."},
        {'icon': 'hardhat', 'title': "Montée en compétence", 'text': "Un réseau qui valorise votre savoir-faire."},
    ],
    'society': [
        {'icon': 'users', 'title': "Emploi des jeunes", 'text': "Des opportunités pour les techniciens de demain."},
        {'icon': 'leaf', 'title': "Énergies propres", 'text': "Un appui concret à la transition énergétique."},
        {'icon': 'sun', 'title': "Accès à l'électricité", 'text': "Des installations qui durent et qui éclairent."},
    ],
}

TESTIMONIALS = [
    {'name': 'Aminata Traoré', 'role': 'Particulier', 'city': 'Bamako, Hamdallaye', 'rating': 5,
     'text': "Panne en pleine soirée, technicien arrivé en 40 minutes. Tout a été réparé proprement et le suivi sur la carte rassure vraiment."},
    {'name': 'Boubacar Diallo', 'role': "Gérant de commerce", 'city': 'Kati', 'rating': 5,
     'text': "Mon onduleur lâchait sans arrêt. Diagnostic clair, devis affiché avant, paiement Orange Money. Service sérieux."},
    {'name': 'Fatoumata Koné', 'role': 'Restauratrice', 'city': 'Bamako, ACI 2000', 'rating': 4,
     'text': "Installation de nouveaux panneaux pour ma cuisine. Travail soigné et conseils utiles pour réduire ma facture."},
    {'name': 'Ibrahim Cissé', 'role': 'Technicien partenaire', 'city': 'Ségou', 'rating': 5,
     'text': "Depuis que j'ai rejoint le réseau, je reçois des missions chaque semaine. La gestion des interventions est simple."},
]

FAQ = [
    {'q': "Comment demander un dépannage ?",
     'a': "Créez un compte client, décrivez votre panne, indiquez votre position et envoyez la demande. Un technicien qualifié vous est affecté selon la proximité, la disponibilité et les compétences requises."},
    {'q': "Quels moyens de paiement sont acceptés ?",
     'a': "Vous réglez par Orange Money, Moov Money ou en espèces. Le paiement en espèces est confirmé dans l'interface après l'intervention."},
    {'q': "Puis-je suivre le technicien en temps réel ?",
     'a': "Oui. Une fois la mission acceptée, vous suivez la progression et l'heure d'arrivée estimée sur une carte, jusqu'à la fin de l'intervention."},
    {'q': "Comment devenir technicien sur la plateforme ?",
     'a': "Créez un compte technicien, renseignez vos compétences et vos zones, puis déposez vos documents. Un administrateur valide votre profil avant que vous receviez des missions."},
    {'q': "L'estimation de coût est-elle définitive ?",
     'a': "Non, c'est une fourchette indicative basée sur le type de service et l'urgence. Le montant final est confirmé avec le technicien selon le travail réellement effectué."},
    {'q': "Dans quelles villes le service est-il disponible ?",
     'a': "Le réseau couvre Bamako et s'étend progressivement aux principales villes du Mali, dont Kati, Ségou et Koulikoro."},
]

# Galerie qui défile (slides)
GALLERY = [
    {'img': 'equipe-bureau', 'title': "Coordination d'équipe", 'sub': "Planification et suivi des interventions"},
    {'img': 'controle-maintenance', 'title': "Contrôle et maintenance", 'sub': "Onduleurs, régulateurs, câblage"},
    {'img': 'team-station', 'title': "Formation solaire", 'sub': "Intervention en équipe sur site"},
    {'img': 'panels-roof', 'title': "Optimisation de production", 'sub': "Nettoyage et réglage des panneaux"},
    {'img': 'tech-check', 'title': "Diagnostic de panne", 'sub': "Identification rapide et sécurisée"},
]
