"""
Serializers for vessel tracking module
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vessel, VesselPosition, VesselNote, VesselRoute

User = get_user_model()


class VesselListSerializer(serializers.ModelSerializer):
    """Serializer for vessel list view (minimal data)"""
    
    current_coordinates = serializers.SerializerMethodField()
    distance_from_destination = serializers.SerializerMethodField()
    
    class Meta:
        model = Vessel
        fields = [
            'id', 'mmsi', 'imo_number', 'vessel_name', 'vessel_type',
            'flag_country', 'status', 'current_coordinates',
            'speed_over_ground', 'destination', 'eta',
            'last_position_update', 'is_tracked', 'distance_from_destination'
        ]
    
    def get_current_coordinates(self, obj):
        """Get current position as [lat, lon]"""
        coords = obj.get_current_coordinates()
        return list(coords) if coords else None
    
    def get_distance_from_destination(self, obj):
        """Calculate distance to destination (placeholder)"""
        # TODO: Implement geospatial calculation
        return None


class VesselDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed vessel view"""
    
    current_coordinates = serializers.SerializerMethodField()
    recent_positions = serializers.SerializerMethodField()
    notes_count = serializers.SerializerMethodField()
    active_route = serializers.SerializerMethodField()
    
    class Meta:
        model = Vessel
        fields = [
            'id', 'mmsi', 'imo_number', 'vessel_name', 'call_sign',
            'vessel_type', 'flag_country', 'built_year', 'gross_tonnage',
            'deadweight', 'length_overall', 'beam', 'draft',
            'status', 'current_coordinates', 'latitude', 'longitude',
            'speed_over_ground', 'course_over_ground', 'heading',
            'destination', 'eta', 'last_position_update',
            'data_source', 'ais_update_frequency', 'is_tracked',
            'notes', 'created_at', 'updated_at',
            'recent_positions', 'notes_count', 'active_route'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_position_update']
    
    def get_current_coordinates(self, obj):
        """Get current position as [lat, lon]"""
        coords = obj.get_current_coordinates()
        return list(coords) if coords else None
    
    def get_recent_positions(self, obj):
        """Get last 10 positions"""
        positions = obj.position_history.all()[:10]
        return VesselPositionSerializer(positions, many=True).data
    
    def get_notes_count(self, obj):
        """Count of notes on this vessel"""
        return obj.notes.count()
    
    def get_active_route(self, obj):
        """Get active route if exists"""
        route = obj.routes.filter(is_active=True).first()
        return VesselRouteSerializer(route).data if route else None


class VesselCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating vessels"""
    
    class Meta:
        model = Vessel
        fields = [
            'mmsi', 'imo_number', 'vessel_name', 'call_sign',
            'vessel_type', 'flag_country', 'built_year', 'gross_tonnage',
            'deadweight', 'length_overall', 'beam', 'draft',
            'status', 'latitude', 'longitude', 'speed_over_ground',
            'course_over_ground', 'heading', 'destination', 'eta',
            'data_source', 'ais_update_frequency', 'is_tracked', 'notes'
        ]
    
    def validate_mmsi(self, value):
        """Validate MMSI is 9 digits"""
        if not value.isdigit() or len(value) != 9:
            raise serializers.ValidationError("MMSI must be exactly 9 digits")
        return value
    
    def validate_imo_number(self, value):
        """Validate IMO number is 7 digits"""
        if value and (not value.isdigit() or len(value) != 7):
            raise serializers.ValidationError("IMO number must be exactly 7 digits")
        return value


class VesselPositionSerializer(serializers.ModelSerializer):
    """Serializer for vessel position data"""
    
    vessel_name = serializers.CharField(source='vessel.vessel_name', read_only=True)
    coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = VesselPosition
        fields = [
            'id', 'vessel', 'vessel_name', 'coordinates',
            'latitude', 'longitude', 'speed_over_ground',
            'course_over_ground', 'heading', 'navigational_status',
            'timestamp', 'received_at', 'data_source'
        ]
        read_only_fields = ['received_at']
    
    def get_coordinates(self, obj):
        """Get position as [lat, lon]"""
        return [float(obj.latitude), float(obj.longitude)]


class VesselPositionBulkSerializer(serializers.Serializer):
    """Serializer for bulk position updates"""
    
    mmsi = serializers.CharField(max_length=9)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    speed_over_ground = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    course_over_ground = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    heading = serializers.IntegerField(required=False)
    navigational_status = serializers.CharField(max_length=50, required=False)
    timestamp = serializers.DateTimeField()
    
    def validate_mmsi(self, value):
        """Validate vessel exists"""
        if not Vessel.objects.filter(mmsi=value).exists():
            raise serializers.ValidationError(f"Vessel with MMSI {value} not found")
        return value


class VesselNoteSerializer(serializers.ModelSerializer):
    """Serializer for vessel notes"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    vessel_name = serializers.CharField(source='vessel.vessel_name', read_only=True)
    
    class Meta:
        model = VesselNote
        fields = [
            'id', 'vessel', 'vessel_name', 'user', 'user_email', 'user_name',
            'title', 'content', 'is_important', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        """Get user's full name"""
        return obj.user.get_full_name() if obj.user else 'Unknown'
    
    def create(self, validated_data):
        """Set user from request context"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class VesselRouteSerializer(serializers.ModelSerializer):
    """Serializer for vessel routes"""
    
    vessel_name = serializers.CharField(source='vessel.vessel_name', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    waypoint_count = serializers.SerializerMethodField()
    
    class Meta:
        model = VesselRoute
        fields = [
            'id', 'vessel', 'vessel_name', 'created_by', 'created_by_name',
            'route_name', 'origin', 'destination', 'waypoints',
            'planned_departure', 'planned_arrival', 'estimated_distance_nm',
            'is_active', 'notes', 'waypoint_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        """Get creator's full name"""
        return obj.created_by.get_full_name() if obj.created_by else 'Unknown'
    
    def get_waypoint_count(self, obj):
        """Count waypoints"""
        return len(obj.waypoints) if obj.waypoints else 0
    
    def create(self, validated_data):
        """Set created_by from request context"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_waypoints(self, value):
        """Validate waypoints format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Waypoints must be a list")
        
        for waypoint in value:
            if not isinstance(waypoint, list) or len(waypoint) != 2:
                raise serializers.ValidationError("Each waypoint must be [latitude, longitude]")
            
            lat, lon = waypoint
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise serializers.ValidationError("Invalid coordinates in waypoint")
        
        return value


class VesselTrackSerializer(serializers.Serializer):
    """Serializer for vessel track (historical positions)"""
    
    vessel_id = serializers.IntegerField()
    vessel_name = serializers.CharField()
    mmsi = serializers.CharField()
    positions = VesselPositionSerializer(many=True)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    total_distance = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    average_speed = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)


class VesselSearchSerializer(serializers.Serializer):
    """Serializer for vessel search parameters"""
    
    query = serializers.CharField(required=False, help_text="Search by name, MMSI, or IMO")
    vessel_type = serializers.ChoiceField(
        choices=Vessel.VESSEL_TYPE_CHOICES,
        required=False
    )
    status = serializers.ChoiceField(
        choices=Vessel.STATUS_CHOICES,
        required=False
    )
    flag_country = serializers.CharField(max_length=2, required=False)
    is_tracked = serializers.BooleanField(required=False, default=None, allow_null=True)
    min_speed = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    max_speed = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
    # Bounding box for map area
    min_lat = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    max_lat = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    min_lon = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    max_lon = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
