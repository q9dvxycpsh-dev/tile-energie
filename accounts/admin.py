from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (ClientProfile, Skill, TechnicianDocument,
                     TechnicianProfile, User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'display_name', 'email', 'role', 'phone',
                    'is_suspended', 'is_staff')
    list_filter = ('role', 'is_suspended', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profil TILE', {'fields': ('role', 'phone', 'city', 'avatar', 'is_suspended')}),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}


class TechnicianDocumentInline(admin.TabularInline):
    model = TechnicianDocument
    extra = 0


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification', 'availability', 'rating_avg',
                    'completed_missions', 'experience_years')
    list_filter = ('verification', 'availability')
    filter_horizontal = ('skills',)
    inlines = [TechnicianDocumentInline]


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'installation_note')
