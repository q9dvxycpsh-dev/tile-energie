from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import ClientProfile, Skill, TechnicianProfile

User = get_user_model()


class RegisterForm(forms.ModelForm):
    ROLE_CHOICES = [
        (User.Role.CLIENT, 'Client'),
        (User.Role.TECHNICIEN, 'Technicien'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial=User.Role.CLIENT)
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(
        attrs={'placeholder': '8 caractères minimum'}))
    password2 = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput(
        attrs={'placeholder': 'Retapez le mot de passe'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Nom'}),
            'email': forms.EmailInput(attrs={'placeholder': 'vous@exemple.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+223 ...'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise ValidationError("Un compte existe déjà avec cet email.")
        return email

    def clean_password1(self):
        pw = self.cleaned_data.get('password1')
        validate_password(pw)
        return pw

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') and cleaned.get('password2') and cleaned['password1'] != cleaned['password2']:
            self.add_error('password2', "Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            if user.is_technicien:
                TechnicianProfile.objects.create(user=user)
            else:
                ClientProfile.objects.create(user=user)
        return user


class TileLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs.update({'placeholder': 'vous@exemple.com', 'autofocus': True})
        self.fields['password'].widget.attrs.update({'placeholder': 'Votre mot de passe'})


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'city', 'avatar']


class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ['address', 'installation_note']
        widgets = {
            'address': forms.TextInput(attrs={'placeholder': 'Quartier, ville'}),
            'installation_note': forms.TextInput(attrs={'placeholder': 'Ex : 4 panneaux, 2 batteries'}),
        }


class TechnicianProfileForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(), required=False,
        widget=forms.CheckboxSelectMultiple, label='Compétences')

    class Meta:
        model = TechnicianProfile
        fields = ['bio', 'skills', 'zones', 'experience_years', 'hourly_indication']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Présentez votre savoir-faire'}),
            'zones': forms.TextInput(attrs={'placeholder': 'Ex : Bamako, Kati'}),
        }
