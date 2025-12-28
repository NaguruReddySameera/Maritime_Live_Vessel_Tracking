from rest_framework import serializers
from .models import Notification, NotificationSettings, UserPreferences


class NotificationSerializer(serializers.ModelSerializer):
    vessel_id = serializers.IntegerField(source='vessel.id', read_only=True, allow_null=True)
    vessel_name = serializers.CharField(source='vessel.vessel_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message',
            'vessel_id', 'vessel_name', 'is_read',
            'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at', 'vessel_id', 'vessel_name']


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = [
            'id', 'email_notifications', 'push_notifications',
            'vessel_status_changes', 'speed_alerts', 'geofence_alerts',
            'maintenance_reminders', 'position_updates_frequency',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserPreferencesSerializer(serializers.ModelSerializer):
    theme_choices = serializers.SerializerMethodField()
    language_choices = serializers.SerializerMethodField()
    timezone_choices = serializers.SerializerMethodField()
    date_format_choices = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPreferences
        fields = [
            'id', 'theme', 'language', 'timezone', 'date_format',
            'theme_choices', 'language_choices', 'timezone_choices', 'date_format_choices',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 
                           'theme_choices', 'language_choices', 'timezone_choices', 'date_format_choices']
    
    def get_theme_choices(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in UserPreferences.THEME_CHOICES]
    
    def get_language_choices(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in UserPreferences.LANGUAGE_CHOICES]
    
    def get_timezone_choices(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in UserPreferences.TIMEZONE_CHOICES]
    
    def get_date_format_choices(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in UserPreferences.DATE_FORMAT_CHOICES]
