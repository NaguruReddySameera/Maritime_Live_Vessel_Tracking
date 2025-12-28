"""
Celery tasks for vessel tracking
"""

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_vessel_positions():
    """
    Fetch and update vessel positions from AIS data provider
    Runs every 60 seconds
    """
    from .models import Vessel
    from .services import AISIntegrationService, VesselService
    
    ais_service = AISIntegrationService()
    tracked_vessels = Vessel.objects.filter(is_tracked=True, is_deleted=False)
    
    updated_count = 0
    error_count = 0
    
    for vessel in tracked_vessels:
        try:
            position_data = ais_service.fetch_vessel_position(vessel.mmsi)
            
            if position_data:
                VesselService.update_vessel_position(vessel, position_data)
                updated_count += 1
            else:
                logger.warning(f"No position data returned for vessel {vessel.mmsi}")
                
        except Exception as e:
            error_count += 1
            logger.error(f"Error updating vessel {vessel.mmsi}: {str(e)}")
    
    logger.info(f"Vessel position update completed: {updated_count} updated, {error_count} errors")
    return f"Updated {updated_count} vessels, {error_count} errors"


@shared_task
def cleanup_old_positions():
    """
    Clean up vessel positions older than 90 days
    Runs daily
    """
    from .models import VesselPosition
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count = VesselPosition.objects.filter(timestamp__lt=cutoff_date).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old vessel positions")
    return f"Deleted {deleted_count} position records"


@shared_task
def check_vessel_tracking_status():
    """
    Check for vessels that haven't reported position in 24 hours
    Send alerts if needed
    """
    from .models import Vessel
    from datetime import timedelta
    
    threshold = timezone.now() - timedelta(hours=24)
    stale_vessels = Vessel.objects.filter(
        is_tracked=True,
        is_deleted=False,
        last_position_update__lt=threshold
    )
    
    if stale_vessels.exists():
        vessel_names = ', '.join([v.vessel_name for v in stale_vessels[:5]])
        logger.warning(f"Found {stale_vessels.count()} vessels with stale position data: {vessel_names}")
        
        # TODO: Send notification/alert
    
    return f"Found {stale_vessels.count()} vessels with stale position data"
