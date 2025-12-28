"""
Views for vessel tracking module
Implements all vessel-related API endpoints
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import logging

from apps.authentication.permissions import IsOperator, IsAnalyst, IsAdmin
from .models import Vessel, VesselPosition, VesselNote, VesselRoute
from .serializers import (
    VesselListSerializer, VesselDetailSerializer, VesselCreateUpdateSerializer,
    VesselPositionSerializer, VesselPositionBulkSerializer,
    VesselNoteSerializer, VesselRouteSerializer,
    VesselTrackSerializer, VesselSearchSerializer
)
from .services import VesselService, AISIntegrationService, VesselAnalyticsService
from .analytics import VesselAnalytics

logger = logging.getLogger(__name__)


class VesselViewSet(viewsets.ModelViewSet):
    """
    ViewSet for vessel management
    
    Permissions:
    - List/Retrieve: Operator, Analyst, Admin
    - Create/Update/Delete: Admin only
    """
    
    queryset = Vessel.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, IsOperator]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['vessel_name', 'mmsi', 'imo_number', 'call_sign']
    ordering_fields = ['vessel_name', 'last_position_update', 'speed_over_ground']
    ordering = ['-last_position_update']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return VesselListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return VesselCreateUpdateSerializer
        return VesselDetailSerializer
    
    def get_permissions(self):
        """Admin only for create/update/delete"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return super().get_permissions()
    
    def list(self, request, *args, **kwargs):
        """List vessels with optional filters"""
        # Apply custom filters
        filters_serializer = VesselSearchSerializer(data=request.query_params)
        if filters_serializer.is_valid():
            queryset = VesselService.search_vessels(filters_serializer.validated_data)
        else:
            queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            # Wrap in success format
            paginated_response.data = {
                'success': True,
                'data': paginated_response.data
            }
            return paginated_response
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get vessel details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Create new vessel"""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        vessel = serializer.save()
        
        logger.info(f"Vessel created: {vessel.vessel_name} (MMSI: {vessel.mmsi}) by {request.user.email}")
        
        return Response({
            'success': True,
            'data': VesselDetailSerializer(vessel).data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update vessel"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        vessel = serializer.save()
        
        logger.info(f"Vessel updated: {vessel.vessel_name} by {request.user.email}")
        
        return Response({
            'success': True,
            'data': VesselDetailSerializer(vessel).data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete vessel"""
        instance = self.get_object()
        instance.soft_delete()
        
        logger.info(f"Vessel deleted: {instance.vessel_name} by {request.user.email}")
        
        return Response({
            'success': True,
            'data': {
                'message': 'Vessel deleted successfully'
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsOperator])
    def track(self, request, pk=None):
        """
        Get historical track for a vessel
        GET /api/vessels/{id}/track/?start=2024-01-01&end=2024-01-31
        """
        vessel = self.get_object()
        
        # Parse date parameters
        start_str = request.query_params.get('start')
        end_str = request.query_params.get('end')
        
        start_time = None
        end_time = None
        
        if start_str:
            try:
                start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            except ValueError:
                return Response({
                    'success': False,
                    'error': {'message': 'Invalid start date format'}
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if end_str:
            try:
                end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            except ValueError:
                return Response({
                    'success': False,
                    'error': {'message': 'Invalid end date format'}
                }, status=status.HTTP_400_BAD_REQUEST)
        
        track_data = VesselService.get_vessel_track(vessel.id, start_time, end_time)
        
        if not track_data:
            return Response({
                'success': False,
                'error': {'message': 'No track data available'}
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = VesselTrackSerializer(track_data)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def update_position(self, request, pk=None):
        """
        Manually update vessel position
        POST /api/vessels/{id}/update_position/
        """
        vessel = self.get_object()
        serializer = VesselPositionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        position_data = serializer.validated_data
        position_data['data_source'] = 'manual'
        
        position = VesselService.update_vessel_position(vessel, position_data)
        
        return Response({
            'success': True,
            'data': {
                'message': 'Position updated successfully',
                'position': VesselPositionSerializer(position).data
            }
        })
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsAnalyst])
    def statistics(self, request, pk=None):
        """
        Get vessel statistics
        GET /api/vessels/{id}/statistics/?days=30
        """
        vessel = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        stats = VesselAnalyticsService.get_vessel_statistics(vessel.id, days)
        
        return Response({
            'success': True,
            'data': stats
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsOperator])
    def map_view(self, request):
        """
        Get vessels in a bounding box for map display
        GET /api/vessels/map_view/?min_lat=...&max_lat=...&min_lon=...&max_lon=...
        """
        try:
            min_lat = float(request.query_params.get('min_lat'))
            max_lat = float(request.query_params.get('max_lat'))
            min_lon = float(request.query_params.get('min_lon'))
            max_lon = float(request.query_params.get('max_lon'))
        except (TypeError, ValueError):
            return Response({
                'success': False,
                'error': {'message': 'Invalid bounding box coordinates'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        vessels = VesselService.get_vessels_in_area(min_lat, max_lat, min_lon, max_lon)
        serializer = VesselListSerializer(vessels, many=True)
        
        return Response({
            'success': True,
            'data': {
                'count': vessels.count(),
                'vessels': serializer.data
            }
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def bulk_update_positions(self, request):
        """
        Bulk update vessel positions (for AIS integration)
        POST /api/vessels/bulk_update_positions/
        """
        serializer = VesselPositionBulkSerializer(data=request.data, many=True)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = VesselService.bulk_update_positions(serializer.validated_data)
        
        return Response({
            'success': True,
            'data': result
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAnalyst])
    def fleet_statistics(self, request):
        """
        Get overall fleet statistics
        GET /api/vessels/fleet_statistics/
        """
        stats = VesselAnalyticsService.get_fleet_statistics()
        
        return Response({
            'success': True,
            'data': stats
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsOperator])
    def analytics(self, request):
        """
        Get comprehensive analytics data
        GET /api/vessels/analytics/
        """
        try:
            analytics_data = {
                'vessel_statistics': VesselAnalytics.get_vessel_statistics(),
                'speed_analytics': VesselAnalytics.get_speed_analytics(),
                'activity_timeline': VesselAnalytics.get_activity_timeline(),
                'notification_analytics': VesselAnalytics.get_notification_analytics(),
                'fleet_overview': VesselAnalytics.get_fleet_overview(),
                'destination_analytics': VesselAnalytics.get_destination_analytics(),
            }
            
            return Response({
                'success': True,
                'data': analytics_data
            })
        except Exception as e:
            logger.error(f"Error generating analytics: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'message': 'Failed to generate analytics',
                    'details': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsOperator])
    def realtime_positions(self, request):
        """
        Get real-time positions for all tracked vessels from AIS data
        Uses FREE AISHub API for live vessel tracking
        GET /api/vessels/realtime_positions/?min_lat=XX&max_lat=XX&min_lon=XX&max_lon=XX
        """
        try:
            # Get bounding box from query params (default to global if not provided)
            min_lat = float(request.query_params.get('min_lat', -90))
            max_lat = float(request.query_params.get('max_lat', 90))
            min_lon = float(request.query_params.get('min_lon', -180))
            max_lon = float(request.query_params.get('max_lon', 180))
            
            # Fetch real-time data from AIS sources
            ais_service = AISIntegrationService()
            vessels = ais_service.fetch_vessels_in_area(min_lat, max_lat, min_lon, max_lon)
            
            logger.info(f"Fetched {len(vessels)} vessels from AIS data sources")
            
            return Response({
                'success': True,
                'data': {
                    'vessels': vessels,
                    'count': len(vessels),
                    'source': 'aishub_free',
                    'timestamp': timezone.now().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error fetching real-time positions: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'message': 'Failed to fetch real-time vessel positions',
                    'details': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOperator])
    def update_from_ais(self, request, pk=None):
        """
        Update a vessel's position from live AIS data
        POST /api/vessels/{id}/update_from_ais/
        """
        try:
            vessel = self.get_object()
            
            if not vessel.mmsi:
                return Response({
                    'success': False,
                    'error': {
                        'message': 'Vessel must have an MMSI number to fetch AIS data'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Fetch latest position from AIS
            ais_service = AISIntegrationService()
            position_data = ais_service.fetch_vessel_position(vessel.mmsi)
            
            if not position_data:
                return Response({
                    'success': False,
                    'error': {
                        'message': 'No AIS data available for this vessel'
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Update vessel with latest data
            vessel.latitude = position_data['latitude']
            vessel.longitude = position_data['longitude']
            vessel.speed_over_ground = position_data['speed_over_ground']
            vessel.course_over_ground = position_data['course_over_ground']
            vessel.heading = position_data['heading']
            vessel.navigational_status = position_data.get('navigational_status', vessel.navigational_status)
            vessel.last_position_update = timezone.now()
            vessel.data_source = position_data['data_source']
            
            # Update vessel name if available and not set
            if not vessel.vessel_name and position_data.get('vessel_name'):
                vessel.vessel_name = position_data['vessel_name']
            
            vessel.save()
            
            # Create position history record
            VesselPosition.objects.create(
                vessel=vessel,
                latitude=position_data['latitude'],
                longitude=position_data['longitude'],
                speed_over_ground=position_data['speed_over_ground'],
                course_over_ground=position_data['course_over_ground'],
                heading=position_data['heading'],
                timestamp=timezone.now(),
                data_source=position_data['data_source']
            )
            
            serializer = VesselDetailSerializer(vessel)
            
            return Response({
                'success': True,
                'data': {
                    'vessel': serializer.data,
                    'message': f'Vessel position updated from {position_data["data_source"]}'
                }
            })
            
        except Exception as e:
            logger.error(f"Error updating vessel from AIS: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'message': 'Failed to update vessel from AIS data',
                    'details': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VesselPositionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for vessel position history (read-only)
    """
    
    queryset = VesselPosition.objects.all()
    serializer_class = VesselPositionSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    filterset_fields = ['vessel', 'data_source']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def list(self, request, *args, **kwargs):
        """List positions with filters"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filter by vessel MMSI if provided
        mmsi = request.query_params.get('mmsi')
        if mmsi:
            queryset = queryset.filter(vessel__mmsi=mmsi)
        
        # Filter by time range
        start_time = request.query_params.get('start')
        end_time = request.query_params.get('end')
        
        if start_time:
            queryset = queryset.filter(timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(timestamp__lte=end_time)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class VesselNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for vessel notes
    All authenticated users can create notes
    """
    
    queryset = VesselNote.objects.all()
    serializer_class = VesselNoteSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    filterset_fields = ['vessel', 'user', 'is_important']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter by vessel if provided"""
        queryset = super().get_queryset()
        vessel_id = self.request.query_params.get('vessel_id')
        if vessel_id:
            queryset = queryset.filter(vessel_id=vessel_id)
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List notes"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Create note"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        note = serializer.save()
        
        logger.info(f"Note created on vessel {note.vessel.vessel_name} by {request.user.email}")
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class VesselRouteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for vessel routes
    Analysts and Admins can create/manage routes
    """
    
    queryset = VesselRoute.objects.all()
    serializer_class = VesselRouteSerializer
    permission_classes = [IsAuthenticated, IsAnalyst]
    filterset_fields = ['vessel', 'is_active', 'created_by']
    ordering_fields = ['created_at', 'planned_departure']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter by vessel if provided"""
        queryset = super().get_queryset()
        vessel_id = self.request.query_params.get('vessel_id')
        if vessel_id:
            queryset = queryset.filter(vessel_id=vessel_id)
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List routes"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Create route"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        route = serializer.save()
        
        logger.info(f"Route created: {route.route_name} by {request.user.email}")
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAnalyst])
    def activate(self, request, pk=None):
        """
        Activate a route (deactivates other routes for the same vessel)
        POST /api/vessel-routes/{id}/activate/
        """
        route = self.get_object()
        
        # Deactivate other routes for this vessel
        VesselRoute.objects.filter(vessel=route.vessel, is_active=True).update(is_active=False)
        
        # Activate this route
        route.is_active = True
        route.save()
        
        logger.info(f"Route activated: {route.route_name} by {request.user.email}")
        
        return Response({
            'success': True,
            'data': {
                'message': 'Route activated successfully',
                'route': VesselRouteSerializer(route).data
            }
        })
