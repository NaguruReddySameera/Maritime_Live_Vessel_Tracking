from django.contrib import admin
from .models import Vessel, VesselPosition, VesselNote, VesselRoute


@admin.register(Vessel)
class VesselAdmin(admin.ModelAdmin):
    """Admin interface for Vessel model"""
    
    list_display = [
        'vessel_name', 'mmsi', 'imo_number', 'vessel_type', 
        'flag_country', 'status', 'is_tracked', 'last_position_update'
    ]
    list_filter = ['vessel_type', 'status', 'flag_country', 'is_tracked', 'is_deleted']
    search_fields = ['vessel_name', 'mmsi', 'imo_number', 'call_sign']
    readonly_fields = ['created_at', 'updated_at', 'last_position_update']
    
    fieldsets = (
        ('Identification', {
            'fields': ('mmsi', 'imo_number', 'vessel_name', 'call_sign')
        }),
        ('Vessel Details', {
            'fields': (
                'vessel_type', 'flag_country', 'built_year',
                'gross_tonnage', 'deadweight', 'length_overall', 'beam', 'draft'
            )
        }),
        ('Current Status', {
            'fields': (
                'status', 'latitude', 'longitude', 'speed_over_ground',
                'course_over_ground', 'heading', 'destination', 'eta'
            )
        }),
        ('Tracking', {
            'fields': (
                'is_tracked', 'data_source', 'ais_update_frequency',
                'last_position_update', 'notes'
            )
        }),
        ('Management', {
            'fields': ('is_deleted', 'created_at', 'updated_at')
        }),
    )


@admin.register(VesselPosition)
class VesselPositionAdmin(admin.ModelAdmin):
    """Admin interface for VesselPosition model"""
    
    list_display = [
        'vessel', 'latitude', 'longitude', 'speed_over_ground',
        'timestamp', 'data_source'
    ]
    list_filter = ['data_source', 'timestamp']
    search_fields = ['vessel__vessel_name', 'vessel__mmsi']
    readonly_fields = ['received_at', 'created_at']
    date_hierarchy = 'timestamp'


@admin.register(VesselNote)
class VesselNoteAdmin(admin.ModelAdmin):
    """Admin interface for VesselNote model"""
    
    list_display = ['vessel', 'title', 'user', 'is_important', 'created_at']
    list_filter = ['is_important', 'created_at']
    search_fields = ['vessel__vessel_name', 'title', 'content', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(VesselRoute)
class VesselRouteAdmin(admin.ModelAdmin):
    """Admin interface for VesselRoute model"""
    
    list_display = [
        'route_name', 'vessel', 'origin', 'destination',
        'is_active', 'planned_departure', 'created_by'
    ]
    list_filter = ['is_active', 'planned_departure', 'created_at']
    search_fields = ['route_name', 'vessel__vessel_name', 'origin', 'destination']
    readonly_fields = ['created_at', 'updated_at']
