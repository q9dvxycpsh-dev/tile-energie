from django import forms

from interventions.models import ContactLead
from .models import Order, Product


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactLead
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Votre nom complet'}),
            'email': forms.EmailInput(attrs={'placeholder': 'vous@exemple.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+223 ...'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Objet de votre demande'}),
            'message': forms.Textarea(attrs={'placeholder': 'Expliquez votre besoin en quelques lignes', 'rows': 5}),
        }
