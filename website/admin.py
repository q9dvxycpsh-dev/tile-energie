from django.contrib import admin

from .models import Order, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'stock', 'is_active', 'is_featured')
    list_filter = ('category', 'is_active', 'is_featured')
    list_editable = ('price', 'stock', 'is_active', 'is_featured')
    search_fields = ('name', 'brand', 'short_description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('reference', 'product_name', 'quantity', 'customer_name',
                    'phone', 'state', 'created_at')
    list_filter = ('state',)
    search_fields = ('reference', 'customer_name', 'phone', 'product_name')
