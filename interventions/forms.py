from django import forms

from accounts.models import Skill, TechnicianDocument
from .models import Dispute, InterventionRequest, Payment, Review


class RequestForm(forms.ModelForm):
    skill = forms.ModelChoiceField(queryset=Skill.objects.all(), label='Type de service',
                                   empty_label='Choisir un service')

    class Meta:
        model = InterventionRequest
        fields = ['skill', 'title', 'description', 'urgency', 'address', 'lat', 'lng']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Ex : Plus de courant depuis ce matin'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': "Décrivez la panne ou le besoin avec un maximum de détails"}),
            'urgency': forms.RadioSelect(),
            'address': forms.TextInput(attrs={'placeholder': 'Quartier, rue, point de repère'}),
            'lat': forms.HiddenInput(),
            'lng': forms.HiddenInput(),
        }

    def clean(self):
        cleaned = super().clean()
        # Règle métier : une demande doit contenir une description et une localisation.
        if not cleaned.get('lat') or not cleaned.get('lng'):
            raise forms.ValidationError("Indiquez votre position sur la carte ou activez la géolocalisation.")
        return cleaned


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(min_value=1, max_value=5, widget=forms.HiddenInput())

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Partagez votre expérience (optionnel)'})}


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['method']
        widgets = {'method': forms.RadioSelect()}


class DisputeForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ['reason']
        widgets = {'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': "Expliquez le motif du litige"})}


class TechnicianDocumentForm(forms.ModelForm):
    class Meta:
        model = TechnicianDocument
        fields = ['kind', 'file']
