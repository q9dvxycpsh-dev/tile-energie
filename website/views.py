from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render

from accounts.models import TechnicianProfile
from . import content
from .chatbot import build_tree
from .forms import ContactForm


def _featured_technicians():
    return list(
        TechnicianProfile.objects.filter(
            verification=TechnicianProfile.Verification.VERIFIED
        ).select_related('user').prefetch_related('skills')[:3]
    )


def home(request):
    ctx = {
        'skills': content.SKILLS,
        'steps': content.STEPS,
        'stats': content.STATS,
        'advantages': content.ADVANTAGES,
        'testimonials': content.TESTIMONIALS,
        'gallery': content.GALLERY,
        'faq': content.FAQ[:4],
        'technicians': _featured_technicians(),
    }
    return render(request, 'website/home.html', ctx)


def apropos(request):
    ctx = {
        'skills': content.SKILLS,
        'steps': content.STEPS,
        'advantages': content.ADVANTAGES,
        'stats': content.STATS,
        'objectifs': content.OBJECTIFS,
    }
    return render(request, 'website/apropos.html', ctx)


def calculateur(request):
    return render(request, 'website/calculateur.html', {})


def faq(request):
    return render(request, 'website/faq.html', {'faq': content.FAQ})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Message envoyé. Notre équipe vous répond sous 24 heures.")
            return redirect('website:contact')
        messages.error(request, "Veuillez corriger les champs indiqués.")
    else:
        form = ContactForm()
    return render(request, 'website/contact.html', {'form': form})


def chatbot_api(request):
    """Renvoie l'arbre de l'assistant Tila en JSON (réponses à choisir)."""
    return JsonResponse({'tree': build_tree()})
