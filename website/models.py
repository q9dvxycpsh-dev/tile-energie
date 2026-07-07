"""Mini boutique d'équipement solaire : produits gérables depuis l'admin,
et commandes passées depuis la boutique publique.
"""
import secrets

from django.conf import settings
from django.db import models
from django.utils.text import slugify


CATEGORY_ICON = {
    'panneaux': 'panel',
    'batteries': 'battery',
    'onduleurs': 'plug',
    'regulateurs': 'gauge',
    'kits': 'grid',
    'accessoires': 'settings',
}


class Product(models.Model):
    class Category(models.TextChoices):
        PANNEAU = 'panneaux', 'Panneaux solaires'
        BATTERIE = 'batteries', 'Batteries'
        ONDULEUR = 'onduleurs', 'Onduleurs'
        REGULATEUR = 'regulateurs', 'Régulateurs'
        KIT = 'kits', 'Kits solaires'
        ACCESSOIRE = 'accessoires', 'Accessoires'

    name = models.CharField('Nom', max_length=140)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    category = models.CharField('Catégorie', max_length=14, choices=Category.choices,
                                default=Category.PANNEAU)
    brand = models.CharField('Marque', max_length=80, blank=True)
    short_description = models.CharField('Description courte', max_length=160, blank=True)
    description = models.TextField('Description', blank=True)
    spec = models.CharField('Caractéristique clé', max_length=120, blank=True,
                            help_text='Ex : 450 Wc monocristallin')
    price = models.PositiveIntegerField('Prix (FCFA)', default=0)
    image = models.ImageField('Photo', upload_to='products/', blank=True, null=True)
    stock = models.PositiveIntegerField('Stock', default=0)
    is_active = models.BooleanField('En vente', default=True)
    is_featured = models.BooleanField('Mis en avant', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', 'category', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'produit'
            slug, i = base, 2
            while Product.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f'{base}-{i}'
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def category_icon(self):
        return CATEGORY_ICON.get(self.category, 'panel')


class Order(models.Model):
    class State(models.TextChoices):
        NEW = 'nouvelle', 'Nouvelle'
        CONFIRMED = 'confirmee', 'Confirmée'
        DELIVERED = 'livree', 'Livrée'
        CANCELLED = 'annulee', 'Annulée'

    reference = models.CharField(max_length=16, unique=True, editable=False, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='orders')
    product_name = models.CharField(max_length=160, blank=True)
    quantity = models.PositiveIntegerField('Quantité', default=1)
    unit_price = models.PositiveIntegerField('Prix unitaire (FCFA)', default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='orders')
    customer_name = models.CharField('Nom du client', max_length=120)
    phone = models.CharField('Téléphone', max_length=30)
    address = models.CharField('Adresse de livraison', max_length=200, blank=True)
    note = models.CharField('Remarque', max_length=200, blank=True)
    state = models.CharField(max_length=10, choices=State.choices, default=State.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = 'CMD-' + secrets.token_hex(3).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.reference} · {self.product_name}'

    @property
    def total(self):
        return self.unit_price * self.quantity

    @property
    def tone(self):
        return {'nouvelle': 'info', 'confirmee': 'accent',
                'livree': 'success', 'annulee': 'muted'}.get(self.state, 'muted')
