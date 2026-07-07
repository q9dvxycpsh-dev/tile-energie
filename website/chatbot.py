"""Arbre de décision de l'assistant Tila.

Le chatbot reste un outil d'orientation et de pré-diagnostic de premier niveau,
avec des réponses à choisir. Le contenu vit côté Django et est servi en JSON.
"""
from django.urls import reverse


def build_tree():
    create = reverse('interventions:request_create')
    calc = reverse('website:calculateur')
    register = reverse('accounts:register')
    contact = reverse('website:contact')

    def back(node='start', label='Revenir au menu'):
        return {'label': label, 'go': node}

    return {
        'start': {
            'bot': "Bonjour, je suis <b>Tila</b>, l'assistante de TILE ÉNERGIE. "
                   "Sur quoi puis-je vous aider&nbsp;?",
            'options': [
                {'label': "J'ai une panne solaire", 'go': 'diag'},
                {'label': "Comment ça marche", 'go': 'how'},
                {'label': "Tarifs et paiement", 'go': 'pricing'},
                {'label': "Devenir technicien", 'go': 'tech'},
                {'label': "Parler à un conseiller", 'go': 'human'},
            ],
        },
        'diag': {
            'bot': "Décrivez le symptôme principal et je vous oriente. "
                   "Ceci est un pré-diagnostic, le technicien confirmera sur place.",
            'options': [
                {'label': "Plus de courant du tout", 'go': 'd_power'},
                {'label': "La batterie ne tient pas", 'go': 'd_batt'},
                {'label': "L'onduleur s'arrête ou bipe", 'go': 'd_inv'},
                {'label': "Panneaux sales ou abîmés", 'go': 'd_panel'},
                back(),
            ],
        },
        'd_power': {
            'bot': "Coupure totale. Vérifiez d'abord le disjoncteur et les fusibles du "
                   "régulateur. Si tout est en place, il s'agit souvent du régulateur ou "
                   "d'un câble débranché. Un <b>diagnostic</b> sur site est recommandé.",
            'options': [
                {'label': "Demander un technicien", 'url': create},
                back('diag', 'Autre symptôme'), back(),
            ],
        },
        'd_batt': {
            'bot': "Autonomie en baisse. La batterie est peut-être en fin de vie ou mal "
                   "chargée par le régulateur. Notez l'âge de la batterie&nbsp;: au-delà de "
                   "3 à 5 ans, un remplacement est fréquent.",
            'options': [
                {'label': "Demander un technicien", 'url': create},
                {'label': "Dimensionner mon parc batterie", 'url': calc},
                back(),
            ],
        },
        'd_inv': {
            'bot': "Un onduleur qui bipe signale souvent une surcharge ou une batterie "
                   "faible. Débranchez les appareils les plus gourmands puis réessayez. "
                   "Si le défaut persiste, l'onduleur doit être contrôlé.",
            'options': [
                {'label': "Demander un technicien", 'url': create},
                back('diag', 'Autre symptôme'), back(),
            ],
        },
        'd_panel': {
            'bot': "Des panneaux encrassés peuvent perdre 15 à 25&nbsp;% de rendement. "
                   "Un nettoyage et un contrôle des fixations suffisent souvent. En cas de "
                   "vitre fissurée, le panneau concerné est à remplacer.",
            'options': [
                {'label': "Demander une maintenance", 'url': create},
                back('diag', 'Autre symptôme'), back(),
            ],
        },
        'how': {
            'bot': "En 4 étapes&nbsp;: vous décrivez la panne et votre position, la "
                   "plateforme affecte le technicien qualifié le plus proche, vous suivez "
                   "son arrivée en temps réel, puis vous payez et notez le service.",
            'options': [
                {'label': "Demander un dépannage", 'url': create},
                {'label': "Estimer mon installation", 'url': calc},
                back(),
            ],
        },
        'pricing': {
            'bot': "Vous voyez une estimation indicative avant d'envoyer la demande. "
                   "Le paiement se fait par <b>Orange Money</b>, <b>Moov Money</b> ou en "
                   "espèces, confirmé après l'intervention.",
            'options': [
                {'label': "Estimer un coût", 'url': calc},
                {'label': "Demander un dépannage", 'url': create},
                back(),
            ],
        },
        'tech': {
            'bot': "Vous êtes technicien solaire&nbsp;? Rejoignez le réseau, recevez des "
                   "missions près de chez vous et développez votre activité. La validation "
                   "de votre profil se fait après dépôt de vos documents.",
            'options': [
                {'label': "Créer un compte technicien", 'url': register},
                back(),
            ],
        },
        'human': {
            'bot': "Notre équipe répond 7j/7 de 7h à 21h. Vous pouvez nous écrire depuis "
                   "la page contact ou nous appeler directement.",
            'options': [
                {'label': "Ouvrir la page contact", 'url': contact},
                back(),
            ],
        },
    }
