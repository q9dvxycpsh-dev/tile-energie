from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from interventions.models import ActivityLog
from .forms import (ClientProfileForm, ProfileForm, RegisterForm,
                    TechnicianProfileForm, TileLoginForm)


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:redirect_after_login')
    role = request.GET.get('role')
    initial = {'role': role} if role in ('client', 'technicien') else {}
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            ActivityLog.record(user, 'Création de compte', user.get_role_display())
            messages.success(request, "Bienvenue chez TILE ÉNERGIE. Votre compte est créé.")
            return redirect('accounts:redirect_after_login')
        messages.error(request, "Le formulaire contient des erreurs.")
    else:
        form = RegisterForm(initial=initial)
    return render(request, 'accounts/register.html', {'form': form})


class TileLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = TileLoginForm
    redirect_authenticated_user = True


@login_required
def redirect_after_login(request):
    user = request.user
    if user.is_suspended and not user.is_superuser:
        messages.error(request, "Votre compte est suspendu. Contactez l'administration.")
    if user.is_platform_admin:
        return redirect('interventions:admin_dashboard')
    if user.is_technicien:
        return redirect('interventions:tech_dashboard')
    return redirect('interventions:client_dashboard')


@login_required
def profile(request):
    user = request.user
    pform = ProfileForm(request.POST or None, request.FILES or None, instance=user)
    extra = None
    if user.is_technicien and hasattr(user, 'technician_profile'):
        extra = TechnicianProfileForm(request.POST or None, instance=user.technician_profile)
    elif user.is_client and hasattr(user, 'client_profile'):
        extra = ClientProfileForm(request.POST or None, instance=user.client_profile)

    if request.method == 'POST':
        ok = pform.is_valid() and (extra is None or extra.is_valid())
        if ok:
            pform.save()
            if extra:
                extra.save()
            messages.success(request, "Profil mis à jour.")
            return redirect('accounts:profile')
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")

    return render(request, 'accounts/profile.html', {'pform': pform, 'extra': extra})
