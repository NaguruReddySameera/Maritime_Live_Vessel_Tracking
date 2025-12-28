"""
Service layer for vessel tracking
Handles AIS integration and business logic
"""

from django.utils import timezone
from django.db.models import Q, Avg, Count
from decimal import Decimal
import logging
import requests
from django.conf import settings

from .models import Vessel, VesselPosition, VesselNote, VesselRoute

logger = logging.getLogger(__name__)


class VesselService:
    """
    Service class for vessel-related business logic
    """
    
    @staticmethod
    def search_vessels(filters):
        """
        Search vessels with multiple filters
        """
        queryset = Vessel.objects.filter(is_deleted=False)
        
        # Text search (name, MMSI, IMO)
        if filters.get('query'):
            query = filters['query']
            queryset = queryset.filter(
                Q(vessel_name__icontains=query) |
                Q(mmsi__icontains=query) |
                Q(imo_number__icontains=query)
            )
        
        # Vessel type filter
        if filters.get('vessel_type'):
            queryset = queryset.filter(vessel_type=filters['vessel_type'])
        
        # Status filter
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        # Flag country filter
        if filters.get('flag_country'):
            queryset = queryset.filter(flag_country=filters['flag_country'])
        
        # Tracked status filter
        if filters.get('is_tracked') is not None:
            queryset = queryset.filter(is_tracked=filters['is_tracked'])
        
        # Speed range filter
        if filters.get('min_speed') is not None:
            queryset = queryset.filter(speed_over_ground__gte=filters['min_speed'])
        if filters.get('max_speed') is not None:
            queryset = queryset.filter(speed_over_ground__lte=filters['max_speed'])
        
        # Bounding box filter (for map view)
        if all(k in filters for k in ['min_lat', 'max_lat', 'min_lon', 'max_lon']):
            queryset = queryset.filter(
                latitude__gte=filters['min_lat'],
                latitude__lte=filters['max_lat'],
                longitude__gte=filters['min_lon'],
                longitude__lte=filters['max_lon']
            )
        
        return queryset
    
    @staticmethod
    def get_vessel_track(vessel_id, start_time=None, end_time=None):
        """
        Get historical track for a vessel
        """
        try:
            vessel = Vessel.objects.get(id=vessel_id, is_deleted=False)
        except Vessel.DoesNotExist:
            return None
        
        positions = VesselPosition.objects.filter(vessel=vessel)
        
        if start_time:
            positions = positions.filter(timestamp__gte=start_time)
        if end_time:
            positions = positions.filter(timestamp__lte=end_time)
        
        positions = positions.order_by('timestamp')
        
        # Calculate statistics
        track_data = {
            'vessel_id': vessel.id,
            'vessel_name': vessel.vessel_name,
            'mmsi': vessel.mmsi,
            'positions': positions,
            'start_time': positions.first().timestamp if positions.exists() else None,
            'end_time': positions.last().timestamp if positions.exists() else None,
        }
        
        # Calculate average speed
        avg_speed = positions.aggregate(Avg('speed_over_ground'))['speed_over_ground__avg']
        if avg_speed:
            track_data['average_speed'] = round(Decimal(str(avg_speed)), 2)
        
        return track_data
    
    @staticmethod
    def update_vessel_position(vessel, position_data):
        """
        Update vessel's current position and create historical record
        """
        # Update vessel's current position
        vessel.latitude = position_data['latitude']
        vessel.longitude = position_data['longitude']
        vessel.speed_over_ground = position_data.get('speed_over_ground')
        vessel.course_over_ground = position_data.get('course_over_ground')
        vessel.heading = position_data.get('heading')
        vessel.last_position_update = timezone.now()
        vessel.save(update_fields=[
            'latitude', 'longitude', 'speed_over_ground',
            'course_over_ground', 'heading', 'last_position_update'
        ])
        
        # Create historical position record
        position = VesselPosition.objects.create(
            vessel=vessel,
            latitude=position_data['latitude'],
            longitude=position_data['longitude'],
            speed_over_ground=position_data.get('speed_over_ground'),
            course_over_ground=position_data.get('course_over_ground'),
            heading=position_data.get('heading'),
            navigational_status=position_data.get('navigational_status'),
            timestamp=position_data.get('timestamp', timezone.now()),
            data_source=position_data.get('data_source', 'api')
        )
        
        logger.info(f"Updated position for vessel {vessel.vessel_name} (MMSI: {vessel.mmsi})")
        return position
    
    @staticmethod
    def bulk_update_positions(position_data_list):
        """
        Bulk update vessel positions from AIS data
        """
        updated_count = 0
        errors = []
        
        for data in position_data_list:
            try:
                vessel = Vessel.objects.get(mmsi=data['mmsi'])
                VesselService.update_vessel_position(vessel, data)
                updated_count += 1
            except Vessel.DoesNotExist:
                errors.append(f"Vessel with MMSI {data['mmsi']} not found")
            except Exception as e:
                errors.append(f"Error updating {data.get('mmsi')}: {str(e)}")
                logger.error(f"Error in bulk update: {str(e)}")
        
        logger.info(f"Bulk position update: {updated_count} successful, {len(errors)} errors")
        return {'updated': updated_count, 'errors': errors}
    
    @staticmethod
    def get_vessels_in_area(min_lat, max_lat, min_lon, max_lon):
        """
        Get all vessels in a geographic bounding box
        """
        return Vessel.objects.filter(
            is_deleted=False,
            latitude__gte=min_lat,
            latitude__lte=max_lat,
            longitude__gte=min_lon,
            longitude__lte=max_lon
        )
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """
        Calculate distance between two coordinates using Haversine formula
        Returns distance in nautical miles
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 3440.065  # Earth's radius in nautical miles
        
        lat1_rad = radians(float(lat1))
        lat2_rad = radians(float(lat2))
        lon1_rad = radians(float(lon1))
        lon2_rad = radians(float(lon2))
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        distance = R * c
        return round(distance, 2)


class AISIntegrationService:
    """
    Service for integrating with external AIS data providers
    Supports multiple free AIS data sources:
    - MarineSia API (Free, recommended) - Primary source for vessel positions
    - AISHub (Free, no API key required) - Fallback source
    - AIS Stream (Free tier available)
    - MarineTraffic API (Fallback, requires API key)
    - StormGlass API (For weather data, not vessel tracking)
    """
    
    def __init__(self):
        self.api_key = settings.MARINETRAFFIC_API_KEY
        self.marinesia_api_key = getattr(settings, 'MARINESIA_API_KEY', '')
        self.stormglass_api_key = getattr(settings, 'STORMGLASS_API_KEY', '')
        self.base_url = 'https://services.marinetraffic.com/api'
        self.marinesia_url = 'https://api.marinesia.com/api/v1'
        self.aishub_url = 'http://data.aishub.net/ws.php'
        self.aisstream_url = 'https://stream.aisstream.io/v0'
        self.stormglass_url = 'https://api.stormglass.io/v2'
    
    def fetch_vessel_position(self, mmsi):
        """
        Fetch current position for a vessel by MMSI
        Tries MarineSia (free) first, then AISHub, then MarineTraffic
        """
        # Try MarineSia first (FREE API - Recommended)
        position = self._fetch_from_marinesia(mmsi)
        if position:
            return position
        
        # Try AISHub (FREE - No API key required)
        position = self._fetch_from_aishub(mmsi)
        if position:
            return position
        
        # Try MarineTraffic if API key is configured
        if self.api_key:
            position = self._fetch_from_marinetraffic(mmsi)
            if position:
                return position
        
        # Return mock data for development
        logger.warning(f"Using mock data for MMSI {mmsi}")
        return self._mock_vessel_position(mmsi)
    
    def _fetch_from_marinesia(self, mmsi):
        """
        Fetch vessel data from MarineSia API (FREE service)
        API Docs: https://api.marinesia.com/redoc
        Endpoints:
        - GET /api/v1/vessel/{MMSI}/location/latest - Get latest position
        - GET /api/v1/vessel/{MMSI}/profile - Get vessel profile
        """
        try:
            # Fetch latest location
            url = f"{self.marinesia_url}/vessel/{mmsi}/location/latest"
            params = {}
            if self.marinesia_api_key:
                params['key'] = self.marinesia_api_key
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            location_data = response.json()
            
            # Fetch vessel profile for additional details
            profile_data = None
            try:
                profile_url = f"{self.marinesia_url}/vessel/{mmsi}/profile"
                profile_params = {}
                if self.marinesia_api_key:
                    profile_params['key'] = self.marinesia_api_key
                
                profile_response = requests.get(profile_url, params=profile_params, timeout=10)
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
            except Exception as e:
                logger.debug(f"Could not fetch profile for MMSI {mmsi}: {str(e)}")
            
            if location_data:
                return {
                    'mmsi': str(mmsi),
                    'latitude': float(location_data.get('latitude', 0)),
                    'longitude': float(location_data.get('longitude', 0)),
                    'speed_over_ground': float(location_data.get('speed', 0)) if location_data.get('speed') else 0,
                    'course_over_ground': float(location_data.get('course', 0)) if location_data.get('course') else 0,
                    'heading': int(location_data.get('heading', 0)) if location_data.get('heading') else None,
                    'navigational_status': location_data.get('status', 'unknown'),
                    'timestamp': timezone.now(),
                    'data_source': 'marinesia',
                    'vessel_name': profile_data.get('name', '') if profile_data else location_data.get('name', ''),
                    'vessel_type': profile_data.get('type', '') if profile_data else '',
                    'destination': location_data.get('destination', ''),
                    'eta': location_data.get('eta', '')
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error fetching from MarineSia for MMSI {mmsi}: {str(e)}")
            return None
    
    def _fetch_from_aishub(self, mmsi):
        """
        Fetch vessel data from AISHub (FREE service)
        API Docs: http://www.aishub.net/api
        """
        try:
            params = {
                'username': 'AH_DEMO',  # Free demo access
                'format': 1,  # JSON format
                'output': 'json',
                'compress': 0,
                'mmsi': mmsi
            }
            
            response = requests.get(self.aishub_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and data.get('ERROR') == 'False' and len(data.get('data', [])) > 0:
                vessel_data = data['data'][0]
                return {
                    'mmsi': vessel_data.get('MMSI'),
                    'latitude': float(vessel_data.get('LATITUDE', 0)),
                    'longitude': float(vessel_data.get('LONGITUDE', 0)),
                    'speed_over_ground': float(vessel_data.get('SOG', 0)),
                    'course_over_ground': float(vessel_data.get('COG', 0)),
                    'heading': int(vessel_data.get('HEADING', 0)),
                    'navigational_status': vessel_data.get('NAVSTAT', 'unknown'),
                    'timestamp': timezone.now(),
                    'data_source': 'aishub',
                    'vessel_name': vessel_data.get('NAME', ''),
                    'vessel_type': vessel_data.get('TYPE', ''),
                    'destination': vessel_data.get('DESTINATION', ''),
                    'eta': vessel_data.get('ETA', '')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from AISHub for MMSI {mmsi}: {str(e)}")
            return None
    
    def _fetch_from_marinetraffic(self, mmsi):
        """
        Fetch vessel data from MarineTraffic API (requires paid API key)
        """
        try:
            url = f"{self.base_url}/exportvessel/v:8/{self.api_key}/timespan:10/mmsi:{mmsi}/protocol:json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                vessel_data = data[0]
                return {
                    'mmsi': vessel_data.get('MMSI'),
                    'latitude': vessel_data.get('LAT'),
                    'longitude': vessel_data.get('LON'),
                    'speed_over_ground': vessel_data.get('SPEED'),
                    'course_over_ground': vessel_data.get('COURSE'),
                    'heading': vessel_data.get('HEADING'),
                    'navigational_status': vessel_data.get('STATUS'),
                    'timestamp': timezone.now(),
                    'data_source': 'marinetraffic'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from MarineTraffic for MMSI {mmsi}: {str(e)}")
            return None
    
    def fetch_vessels_in_area(self, min_lat, max_lat, min_lon, max_lon):
        """
        Fetch all vessels in a geographic area
        Uses existing static data first, then enhances with MarineSia/AISHub APIs
        StormGlass API is used for weather data enhancement (not vessel positions)
        """
        # Start with existing static/database vessels in the area
        vessels = self._fetch_static_vessels_in_area(min_lat, max_lat, min_lon, max_lon)
        
        # Try to enhance with MarineSia API data (FREE API - Recommended)
        marinesia_vessels = self._fetch_area_from_marinesia(min_lat, max_lat, min_lon, max_lon)
        if marinesia_vessels:
            logger.info(f"Fetched {len(marinesia_vessels)} vessels from MarineSia")
            # Merge with static vessels (avoid duplicates by MMSI)
            existing_mmsis = {v.get('mmsi') for v in vessels}
            for mv in marinesia_vessels:
                if mv.get('mmsi') not in existing_mmsis:
                    vessels.append(mv)
        
        # Try AISHub (FREE) - Additional source for real vessel positions
        aishub_vessels = self._fetch_area_from_aishub(min_lat, max_lat, min_lon, max_lon)
        if aishub_vessels:
            logger.info(f"Fetched {len(aishub_vessels)} vessels from AISHub")
            # Merge with existing vessels (avoid duplicates by MMSI)
            existing_mmsis = {v.get('mmsi') for v in vessels}
            for av in aishub_vessels:
                if av.get('mmsi') not in existing_mmsis:
                    vessels.append(av)
        
        # Try MarineTraffic if API key is configured
        if self.api_key:
            mt_vessels = self._fetch_area_from_marinetraffic(min_lat, max_lat, min_lon, max_lon)
            if mt_vessels:
                existing_mmsis = {v.get('mmsi') for v in vessels}
                for mtv in mt_vessels:
                    if mtv.get('mmsi') not in existing_mmsis:
                        vessels.append(mtv)
        
        # Enhance with weather data from StormGlass if API key is available
        if vessels and self.stormglass_api_key:
            try:
                vessels = self._enhance_vessels_with_weather(vessels, min_lat, max_lat, min_lon, max_lon)
            except Exception as e:
                logger.warning(f"Failed to enhance with StormGlass weather data: {str(e)}")
        
        logger.info(f"Total {len(vessels)} vessels in area (static + API data)")
        return vessels
    
    def _fetch_static_vessels_in_area(self, min_lat, max_lat, min_lon, max_lon):
        """
        Fetch vessels from database that are within the specified area
        Uses existing static/seed data
        """
        try:
            from .models import Vessel
            
            # Get vessels from database within the bounding box
            db_vessels = Vessel.objects.filter(
                is_deleted=False,
                latitude__gte=min_lat,
                latitude__lte=max_lat,
                longitude__gte=min_lon,
                longitude__lte=max_lon
            )
            
            formatted_vessels = []
            for vessel in db_vessels:
                if vessel.latitude and vessel.longitude:
                    formatted_vessels.append({
                        'mmsi': str(vessel.mmsi),
                        'name': vessel.vessel_name,
                        'latitude': float(vessel.latitude),
                        'longitude': float(vessel.longitude),
                        'speed': float(vessel.speed_over_ground) if vessel.speed_over_ground else 0,
                        'course': float(vessel.course_over_ground) if vessel.course_over_ground else 0,
                        'heading': int(vessel.heading) if vessel.heading else None,
                        'status': vessel.status,
                        'vessel_type': vessel.vessel_type,
                        'destination': vessel.destination or '',
                        'eta': vessel.eta.isoformat() if vessel.eta else '',
                        'timestamp': vessel.last_position_update.isoformat() if vessel.last_position_update else None,
                        'source': 'database'
                    })
            
            if formatted_vessels:
                logger.info(f"Found {len(formatted_vessels)} vessels from database in area")
            
            return formatted_vessels
            
        except Exception as e:
            logger.warning(f"Error fetching static vessels from database: {str(e)}")
            return []
    
    def _fetch_area_from_marinesia(self, min_lat, max_lat, min_lon, max_lon):
        """
        Fetch vessels in an area from MarineSia API (FREE service)
        Note: MarineSia API focuses on individual vessel lookups.
        For area queries, we'll try common endpoints, but fallback to AISHub is recommended.
        """
        try:
            # Try different possible endpoints for area queries
            endpoints_to_try = [
                f"{self.marinesia_url}/vessels/area",
                f"{self.marinesia_url}/vessels/search",
                f"{self.marinesia_url}/vessels",
            ]
            
            params = {
                'min_lat': min_lat,
                'max_lat': max_lat,
                'min_lon': min_lon,
                'max_lon': max_lon,
            }
            if self.marinesia_api_key:
                params['key'] = self.marinesia_api_key
            
            for url in endpoints_to_try:
                try:
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Handle different response formats
                        if isinstance(data, list):
                            vessels_list = data
                        elif isinstance(data, dict) and 'vessels' in data:
                            vessels_list = data['vessels']
                        elif isinstance(data, dict) and 'data' in data:
                            vessels_list = data['data']
                        else:
                            continue
                        
                        formatted_vessels = []
                        for vessel_data in vessels_list:
                            try:
                                # Handle different field name variations
                                lat = float(vessel_data.get('latitude') or vessel_data.get('lat') or 0)
                                lon = float(vessel_data.get('longitude') or vessel_data.get('lon') or vessel_data.get('lng') or 0)
                                
                                # Validate coordinates and check if within bounds
                                if lat == 0 and lon == 0:
                                    continue
                                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                                    continue
                                if not (min_lat <= lat <= max_lat) or not (min_lon <= lon <= max_lon):
                                    continue
                                
                                formatted_vessels.append({
                                    'mmsi': str(vessel_data.get('mmsi', vessel_data.get('MMSI', ''))),
                                    'name': (vessel_data.get('name') or vessel_data.get('shipname') or vessel_data.get('SHIPNAME') or 'Unknown').strip() or f"Vessel {vessel_data.get('mmsi', '')}",
                                    'latitude': lat,
                                    'longitude': lon,
                                    'speed': float(vessel_data.get('speed') or vessel_data.get('SOG') or 0),
                                    'course': float(vessel_data.get('course') or vessel_data.get('COG') or 0),
                                    'heading': int(vessel_data.get('heading') or vessel_data.get('HEADING') or 0) if vessel_data.get('heading') or vessel_data.get('HEADING') else None,
                                    'status': vessel_data.get('status') or vessel_data.get('STATUS') or 'unknown',
                                    'vessel_type': vessel_data.get('type') or vessel_data.get('TYPE') or vessel_data.get('shiptype') or '',
                                    'destination': vessel_data.get('destination') or vessel_data.get('DESTINATION') or '',
                                    'eta': vessel_data.get('eta') or vessel_data.get('ETA') or '',
                                    'timestamp': vessel_data.get('timestamp') or vessel_data.get('TIME'),
                                    'source': 'marinesia'
                                })
                            except (ValueError, TypeError) as e:
                                logger.debug(f"Error parsing MarineSia vessel data: {str(e)}")
                                continue
                        
                        if formatted_vessels:
                            logger.info(f"Fetched {len(formatted_vessels)} vessels from MarineSia")
                            return formatted_vessels
                except requests.exceptions.RequestException:
                    continue
            
            # If no endpoint works, return empty (will fallback to AISHub)
            logger.debug("MarineSia area endpoint not available, will use AISHub fallback")
            return []
            
        except Exception as e:
            logger.debug(f"Error fetching area from MarineSia: {str(e)}")
            return []
    
    def _enhance_vessels_with_weather(self, vessels, min_lat, max_lat, min_lon, max_lon):
        """
        Enhance vessel data with weather information from StormGlass API
        Note: StormGlass provides weather data, not vessel positions
        """
        try:
            # Get weather data for the center of the area
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            
            weather = self._fetch_weather_from_stormglass(center_lat, center_lon)
            
            if weather:
                # Add weather info to each vessel
                for vessel in vessels:
                    vessel['weather'] = weather
                    vessel['weather_source'] = 'stormglass'
                logger.info("Enhanced vessels with StormGlass weather data")
            
            return vessels
        except Exception as e:
            logger.warning(f"Error enhancing vessels with weather: {str(e)}")
            return vessels
    
    def _fetch_weather_from_stormglass(self, lat, lon):
        """
        Fetch marine weather data from StormGlass API
        API Documentation: https://docs.stormglass.io/
        """
        if not self.stormglass_api_key:
            return None
        
        try:
            url = f"{self.stormglass_url}/weather/point"
            params = {
                'lat': lat,
                'lng': lon,
                'params': 'waveHeight,waveDirection,windSpeed,windDirection,airTemperature,waterTemperature',
                'source': 'noaa'
            }
            headers = {
                'Authorization': self.stormglass_api_key
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and 'hours' in data and len(data['hours']) > 0:
                current = data['hours'][0]
                return {
                    'wave_height': current.get('waveHeight', {}).get('noaa', 0),
                    'wave_direction': current.get('waveDirection', {}).get('noaa', 0),
                    'wind_speed': current.get('windSpeed', {}).get('noaa', 0),
                    'wind_direction': current.get('windDirection', {}).get('noaa', 0),
                    'air_temperature': current.get('airTemperature', {}).get('noaa', 0),
                    'water_temperature': current.get('waterTemperature', {}).get('noaa', 0),
                }
            
            return None
        except Exception as e:
            logger.warning(f"Error fetching weather from StormGlass: {str(e)}")
            return None
    
    def _fetch_area_from_aishub(self, min_lat, max_lat, min_lon, max_lon):
        """
        Fetch vessels in an area from AISHub (FREE service)
        Enhanced to fetch more comprehensive real-time AIS data
        """
        try:
            params = {
                'username': 'AH_DEMO',  # Free demo access
                'format': 1,  # JSON format
                'output': 'json',
                'compress': 0,
                'latmin': min_lat,
                'latmax': max_lat,
                'lonmin': min_lon,
                'lonmax': max_lon
            }
            
            response = requests.get(self.aishub_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data and data.get('ERROR') == 'False':
                vessels_data = data.get('data', [])
                formatted_vessels = []
                
                for vessel in vessels_data:
                    try:
                        lat = float(vessel.get('LATITUDE', 0))
                        lon = float(vessel.get('LONGITUDE', 0))
                        
                        # Validate coordinates
                        if lat == 0 and lon == 0:
                            continue
                        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                            continue
                        
                        formatted_vessels.append({
                            'mmsi': str(vessel.get('MMSI', '')),
                            'name': vessel.get('NAME', 'Unknown').strip() or f"Vessel {vessel.get('MMSI', '')}",
                            'latitude': lat,
                            'longitude': lon,
                            'speed': float(vessel.get('SOG', 0)),
                            'course': float(vessel.get('COG', 0)),
                            'heading': int(vessel.get('HEADING', 0)) if vessel.get('HEADING') else None,
                            'status': self._map_nav_status(vessel.get('NAVSTAT', '')),
                            'vessel_type': self._map_vessel_type(vessel.get('TYPE', '')),
                            'destination': vessel.get('DESTINATION', '').strip() or None,
                            'eta': vessel.get('ETA', ''),
                            'timestamp': vessel.get('TIME'),
                            'source': 'aishub'
                        })
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing vessel data: {str(e)}")
                        continue
                
                logger.info(f"Fetched {len(formatted_vessels)} vessels from AISHub")
                return formatted_vessels
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching area from AISHub: {str(e)}")
            return []
    
    def _map_nav_status(self, navstat_code):
        """Map AIS navigational status code to readable status"""
        status_map = {
            '0': 'underway',
            '1': 'at_anchor',
            '2': 'not_under_command',
            '3': 'restricted_maneuverability',
            '4': 'restricted_maneuverability',
            '5': 'moored',
            '6': 'aground',
            '7': 'fishing',
            '8': 'under_sail',
        }
        return status_map.get(str(navstat_code), 'underway')
    
    def _map_vessel_type(self, type_code):
        """Map AIS vessel type code to readable type"""
        # Simplified mapping - AIS type codes are more complex
        type_map = {
            '30': 'fishing',
            '31': 'fishing',
            '32': 'fishing',
            '50': 'military',
            '51': 'military',
            '52': 'military',
            '60': 'passenger',
            '61': 'passenger',
            '70': 'cargo',
            '71': 'cargo',
            '80': 'tanker',
            '81': 'tanker',
        }
        return type_map.get(str(type_code), 'cargo')
    
    def _fetch_area_from_marinetraffic(self, min_lat, max_lat, min_lon, max_lon):
        """
        Fetch vessels in an area from MarineTraffic API
        """
        try:
            url = f"{self.base_url}/exportvessels/v:8/{self.api_key}/"
            url += f"minlat:{min_lat}/maxlat:{max_lat}/minlon:{min_lon}/maxlon:{max_lon}/"
            url += "protocol:json"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching area from MarineTraffic: {str(e)}")
            return []
    
    def _enhance_vessels_with_weather(self, vessels, min_lat, max_lat, min_lon, max_lon):
        """
        Enhance vessel data with weather information from StormGlass API
        Note: StormGlass provides weather data, not vessel positions
        """
        try:
            # Get weather data for the center of the area
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            
            weather = self._fetch_weather_from_stormglass(center_lat, center_lon)
            
            if weather:
                # Add weather info to each vessel
                for vessel in vessels:
                    vessel['weather'] = weather
                    vessel['weather_source'] = 'stormglass'
                logger.info("Enhanced vessels with StormGlass weather data")
            
            return vessels
        except Exception as e:
            logger.warning(f"Error enhancing vessels with weather: {str(e)}")
            return vessels
    
    def _fetch_weather_from_stormglass(self, lat, lon):
        """
        Fetch marine weather data from StormGlass API
        API Documentation: https://docs.stormglass.io/
        """
        if not self.stormglass_api_key:
            return None
        
        try:
            url = f"{self.stormglass_url}/weather/point"
            params = {
                'lat': lat,
                'lng': lon,
                'params': 'waveHeight,waveDirection,windSpeed,windDirection,airTemperature,waterTemperature',
                'source': 'noaa'
            }
            headers = {
                'Authorization': self.stormglass_api_key
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and 'hours' in data and len(data['hours']) > 0:
                current = data['hours'][0]
                return {
                    'wave_height': current.get('waveHeight', {}).get('noaa', 0),
                    'wave_direction': current.get('waveDirection', {}).get('noaa', 0),
                    'wind_speed': current.get('windSpeed', {}).get('noaa', 0),
                    'wind_direction': current.get('windDirection', {}).get('noaa', 0),
                    'air_temperature': current.get('airTemperature', {}).get('noaa', 0),
                    'water_temperature': current.get('waterTemperature', {}).get('noaa', 0),
                }
            
            return None
        except Exception as e:
            logger.warning(f"Error fetching weather from StormGlass: {str(e)}")
            return None
    
    def _mock_vessel_position(self, mmsi):
        """
        Return mock position data for development
        """
        import random
        
        return {
            'mmsi': mmsi,
            'latitude': round(random.uniform(-90, 90), 6),
            'longitude': round(random.uniform(-180, 180), 6),
            'speed_over_ground': round(random.uniform(0, 20), 1),
            'course_over_ground': round(random.uniform(0, 360), 1),
            'heading': random.randint(0, 359),
            'navigational_status': 'underway',
            'timestamp': timezone.now(),
            'data_source': 'mock'
        }


class VesselAnalyticsService:
    """
    Service for vessel analytics and statistics
    """
    
    @staticmethod
    def get_fleet_statistics():
        """
        Get overall fleet statistics
        """
        total_vessels = Vessel.objects.filter(is_deleted=False).count()
        tracked_vessels = Vessel.objects.filter(is_deleted=False, is_tracked=True).count()
        
        by_type = Vessel.objects.filter(is_deleted=False).values('vessel_type').annotate(
            count=Count('id')
        )
        
        by_status = Vessel.objects.filter(is_deleted=False).values('status').annotate(
            count=Count('id')
        )
        
        return {
            'total_vessels': total_vessels,
            'tracked_vessels': tracked_vessels,
            'by_type': list(by_type),
            'by_status': list(by_status),
        }
    
    @staticmethod
    def get_vessel_statistics(vessel_id, days=30):
        """
        Get statistics for a specific vessel
        """
        from datetime import timedelta
        
        vessel = Vessel.objects.get(id=vessel_id)
        cutoff_date = timezone.now() - timedelta(days=days)
        
        positions = VesselPosition.objects.filter(
            vessel=vessel,
            timestamp__gte=cutoff_date
        )
        
        stats = positions.aggregate(
            avg_speed=Avg('speed_over_ground'),
            position_count=Count('id')
        )
        
        return {
            'vessel_id': vessel.id,
            'vessel_name': vessel.vessel_name,
            'period_days': days,
            'average_speed': round(stats['avg_speed'], 2) if stats['avg_speed'] else 0,
            'position_updates': stats['position_count'],
        }
