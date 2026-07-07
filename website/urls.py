from django.urls import path

from . import views

app_name = 'website'

urlpatterns = [
    path('', views.home, name='home'),
    path('le-service/', views.apropos, name='apropos'),
    path('calculateur/', views.calculateur, name='calculateur'),
    path('faq/', views.faq, name='faq'),
    path('contact/', views.contact, name='contact'),
    path('api/assistant/', views.chatbot_api, name='chatbot_api'),
]
