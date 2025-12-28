"""
Vessel models for tracking maritime vessels
Integrates with MarineTraffic/AIS-Hub APIs
"""

from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimeStampedModel, SoftDeleteModel

User = get_user_model()


class Vessel(TimeStampedModel, SoftDeleteModel):
    """
    Vessel model with AIS data integration
    """
    
    VESSEL_TYPE_CHOICES = [
        ('cargo', 'Cargo Ship'),
        ('tanker', 'Tanker'),
        ('passenger', 'Passenger Ship'),
        ('fishing', 'Fishing Vessel'),
        ('tug', 'Tug Boat'),
        ('military', 'Military Vessel'),
        ('sailing', 'Sailing Vessel'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('underway', 'Underway Using Engine'),
        ('at_anchor', 'At Anchor'),
        ('not_under_command', 'Not Under Command'),
        ('restricted_maneuverability', 'Restricted Maneuverability'),
        ('moored', 'Moored'),
        ('aground', 'Aground'),
        ('fishing', 'Engaged in Fishing'),
        ('under_sail', 'Under Way Sailing'),
    ]
    
    # Vessel Identification
    mmsi = models.CharField(max_length=9, unique=True, db_index=True, help_text="Maritime Mobile Service Identity")
    imo_number = models.CharField(max_length=7, unique=True, null=True, blank=True, db_index=True, help_text="International Maritime Organization Number")
    vessel_name = models.CharField(max_length=100, db_index=True)
    call_sign = models.CharField(max_length=10, blank=True, null=True)
    
    # Vessel Details
    vessel_type = models.CharField(max_length=50, choices=VESSEL_TYPE_CHOICES, default='cargo')
    flag_country = models.CharField(max_length=2, help_text="ISO 3166-1 alpha-2 country code")
    built_year = models.IntegerField(null=True, blank=True)
    gross_tonnage = models.IntegerField(null=True, blank=True)
    deadweight = models.IntegerField(null=True, blank=True, help_text="Deadweight Tonnage")
    length_overall = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Length in meters")
    beam = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Width in meters")
    draft = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Draft in meters")
    
    # Current Status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='underway')
    
    # Current Position (from latest AIS data)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    speed_over_ground = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Speed in knots")
    course_over_ground = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Course in degrees")
    heading = models.IntegerField(null=True, blank=True, help_text="Heading in degrees")
    
    # Voyage Information
    destination = models.CharField(max_length=100, blank=True, null=True)
    eta = models.DateTimeField(null=True, blank=True, help_text="Estimated Time of Arrival")
    
    # AIS Data Metadata
    last_position_update = models.DateTimeField(null=True, blank=True)
    data_source = models.CharField(max_length=50, default='manual', help_text="Source of vessel data")
    ais_update_frequency = models.IntegerField(default=60, help_text="AIS update frequency in seconds")
    
    # Management
    is_tracked = models.BooleanField(default=True, help_text="Whether to track this vessel")
    internal_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'vessels'
        verbose_name = 'Vessel'
        verbose_name_plural = 'Vessels'
        ordering = ['-last_position_update']
        indexes = [
            models.Index(fields=['mmsi', 'is_deleted']),
            models.Index(fields=['vessel_type', 'is_tracked']),
            models.Index(fields=['last_position_update']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.vessel_name} (MMSI: {self.mmsi})"
    
    def get_current_coordinates(self):
        """Return current position as tuple"""
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None


class VesselPosition(TimeStampedModel):
    """
    Historical vessel position data (track)
    Stores AIS position reports for voyage replay and analytics
    """
    
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE, related_name='position_history')
    
    # Position Data
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    speed_over_ground = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    course_over_ground = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    heading = models.IntegerField(null=True, blank=True)
    
    # Status
    navigational_status = models.CharField(max_length=50, blank=True, null=True)
    
    # Timestamps
    timestamp = models.DateTimeField(db_index=True, help_text="Position timestamp from AIS")
    received_at = models.DateTimeField(auto_now_add=True, help_text="When data was received by our system")
    
    # Metadata
    data_source = models.CharField(max_length=50, default='ais')
    
    class Meta:
        db_table = 'vessel_positions'
        verbose_name = 'Vessel Position'
        verbose_name_plural = 'Vessel Positions'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vessel', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.vessel.vessel_name} at ({self.latitude}, {self.longitude}) - {self.timestamp}"


class VesselNote(TimeStampedModel):
    """
    User notes about vessels
    Operators can add operational notes and observations
    """
    
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='vessel_notes')
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'vessel_notes'
        verbose_name = 'Vessel Note'
        verbose_name_plural = 'Vessel Notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vessel', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"Note on {self.vessel.vessel_name} by {self.user.email if self.user else 'Unknown'}"


class VesselRoute(TimeStampedModel):
    """
    Planned or historical vessel routes
    For voyage planning and route optimization
    """
    
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE, related_name='routes')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    route_name = models.CharField(max_length=200)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    waypoints = models.JSONField(default=list, help_text="List of route waypoints as [lat, lon] pairs")
    
    planned_departure = models.DateTimeField(null=True, blank=True)
    planned_arrival = models.DateTimeField(null=True, blank=True)
    estimated_distance_nm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Distance in nautical miles")
    
    is_active = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'vessel_routes'
        verbose_name = 'Vessel Route'
        verbose_name_plural = 'Vessel Routes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vessel', 'is_active']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.route_name} for {self.vessel.vessel_name}"
