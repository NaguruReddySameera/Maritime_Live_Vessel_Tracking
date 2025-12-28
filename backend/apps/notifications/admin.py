from django.contrib import admin
from .models import Notification, NotificationSettings, UserPreferences


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'user', 'vessel', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__email', 'vessel__vessel_name']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'email_notifications', 'push_notifications',
        'vessel_status_changes', 'speed_alerts', 'position_updates_frequency'
    ]
    list_filter = ['email_notifications', 'push_notifications']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'language', 'timezone', 'date_format', 'updated_at']
    list_filter = ['theme', 'language', 'timezone']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']

