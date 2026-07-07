from django.contrib import admin

from .models import (ActivityLog, ContactLead, Dispute, InterventionRequest,
                     Mission, Notification, Payment, RequestPhoto, Review,
                     StatusEvent)


class RequestPhotoInline(admin.TabularInline):
    model = RequestPhoto
    extra = 0


class StatusEventInline(admin.TabularInline):
    model = StatusEvent
    extra = 0
    readonly_fields = ('status', 'actor', 'note', 'created_at')


@admin.register(InterventionRequest)
class InterventionRequestAdmin(admin.ModelAdmin):
    list_display = ('reference', 'title', 'client', 'skill', 'urgency',
                    'status', 'estimated_cost', 'created_at')
    list_filter = ('status', 'urgency', 'skill')
    search_fields = ('reference', 'title', 'description', 'client__username')
    inlines = [RequestPhotoInline, StatusEventInline]


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('request', 'technician', 'status', 'final_cost', 'created_at')
    list_filter = ('status',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reference', 'mission', 'method', 'amount', 'state', 'created_at')
    list_filter = ('method', 'state')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('mission', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ('mission', 'opened_by', 'state', 'created_at')
    list_filter = ('state',)


@admin.register(ContactLead)
class ContactLeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'handled', 'created_at')
    list_filter = ('handled',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read',)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('actor', 'verb', 'target', 'created_at')
