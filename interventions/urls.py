from django.urls import path

from . import views

app_name = 'interventions'

urlpatterns = [
    # Client
    path('client/', views.client_dashboard, name='client_dashboard'),
    path('client/demande/nouvelle/', views.request_create, name='request_create'),
    path('client/demande/<int:pk>/', views.request_detail, name='request_detail'),
    path('client/demande/<int:pk>/annuler/', views.request_cancel, name='request_cancel'),
    path('client/demande/<int:pk>/payer/', views.request_pay, name='request_pay'),
    path('client/demande/<int:pk>/evaluer/', views.request_review, name='request_review'),
    path('client/historique/', views.client_history, name='client_history'),

    # Technicien
    path('technicien/', views.tech_dashboard, name='tech_dashboard'),
    path('technicien/demandes/', views.tech_available, name='tech_available'),
    path('technicien/demande/<int:pk>/accepter/', views.mission_accept, name='mission_accept'),
    path('technicien/mission/<int:pk>/', views.mission_detail, name='mission_detail'),
    path('technicien/mission/<int:pk>/avancer/', views.mission_advance, name='mission_advance'),
    path('technicien/mission/<int:pk>/refuser/', views.mission_refuse, name='mission_refuse'),
    path('technicien/disponibilite/', views.tech_availability, name='tech_availability'),
    path('technicien/position/', views.tech_position_update, name='tech_position_update'),
    path('technicien/documents/', views.tech_documents, name='tech_documents'),
    path('technicien/gains/', views.tech_earnings, name='tech_earnings'),

    # Administration
    path('admin-tile/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-tile/techniciens/', views.admin_technicians, name='admin_technicians'),
    path('admin-tile/technicien/<int:pk>/action/', views.admin_tech_action, name='admin_tech_action'),
    path('admin-tile/demandes/', views.admin_requests, name='admin_requests'),
    path('admin-tile/demande/<int:pk>/affecter/', views.admin_assign, name='admin_assign'),
    path('admin-tile/carte/', views.admin_map, name='admin_map'),
    path('admin-tile/paiements/', views.admin_payments, name='admin_payments'),
    path('admin-tile/paiement/<int:pk>/confirmer/', views.admin_payment_confirm, name='admin_payment_confirm'),
    path('admin-tile/litiges/', views.admin_disputes, name='admin_disputes'),
    path('admin-tile/litige/<int:pk>/traiter/', views.admin_dispute_action, name='admin_dispute_action'),
    path('admin-tile/utilisateurs/', views.admin_users, name='admin_users'),
    path('admin-tile/utilisateur/<int:pk>/basculer/', views.admin_user_toggle, name='admin_user_toggle'),

    # Commun + API
    path('notifications/', views.notifications, name='notifications'),
    path('api/positions/', views.positions_api, name='positions_api'),
    path('api/mission/<int:pk>/position/', views.mission_position_api, name='mission_position_api'),
]
