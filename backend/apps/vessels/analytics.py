"""
Analytics module for vessel data
"""
from django.db.models import Count, Avg, Q, Max, Min
from django.utils import timezone
from datetime import timedelta
from apps.vessels.models import Vessel, VesselPosition
from apps.notifications.models import Notification


class VesselAnalytics:
    """Generate analytics data for vessels"""
    
    @staticmethod
    def get_vessel_statistics():
        """Get overall vessel statistics"""
        total_vessels = Vessel.objects.count()
        
        # Count by status
        status_stats = Vessel.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Count by type
        type_stats = Vessel.objects.values('vessel_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Count by country
        country_stats = Vessel.objects.values('flag_country').annotate(
            count=Count('id')
        ).order_by('-count')[:10]  # Top 10 countries
        
        # Active vs Inactive vessels
        active_count = Vessel.objects.filter(is_tracked=True).count()
        inactive_count = total_vessels - active_count
        
        return {
            'total_vessels': total_vessels,
            'active_vessels': active_count,
            'inactive_vessels': inactive_count,
            'by_status': list(status_stats),
            'by_type': list(type_stats),
            'by_country': list(country_stats),
        }
    
    @staticmethod
    def get_speed_analytics():
        """Get speed-related analytics"""
        from decimal import Decimal, InvalidOperation
        
        vessels = Vessel.objects.exclude(
            speed_over_ground__isnull=True
        )
        
        speeds = []
        for vessel in vessels:
            try:
                if vessel.speed_over_ground is not None:
                    speed = float(vessel.speed_over_ground)
                    if 0 <= speed <= 100:  # Reasonable speed range
                        speeds.append(speed)
            except (ValueError, TypeError, InvalidOperation):
                continue
        
        if not speeds:
            return {
                'average_speed': 0.0,
                'max_speed': 0.0,
                'min_speed': 0.0,
                'speed_distribution': [
                    {'range': '0-5', 'count': 0},
                    {'range': '5-10', 'count': 0},
                    {'range': '10-15', 'count': 0},
                    {'range': '15-20', 'count': 0},
                    {'range': '20+', 'count': 0}
                ]
            }
        
        avg_speed = sum(speeds) / len(speeds)
        max_speed = max(speeds)
        min_speed = min(speeds)
        
        # Speed distribution (0-5, 5-10, 10-15, 15-20, 20+)
        distribution = {
            '0-5': 0,
            '5-10': 0,
            '10-15': 0,
            '15-20': 0,
            '20+': 0
        }
        
        for speed in speeds:
            if speed < 5:
                distribution['0-5'] += 1
            elif speed < 10:
                distribution['5-10'] += 1
            elif speed < 15:
                distribution['10-15'] += 1
            elif speed < 20:
                distribution['15-20'] += 1
            else:
                distribution['20+'] += 1
        
        return {
            'average_speed': round(avg_speed, 2),
            'max_speed': round(max_speed, 2),
            'min_speed': round(min_speed, 2),
            'speed_distribution': [
                {'range': k, 'count': v} for k, v in distribution.items()
            ]
        }
    
    @staticmethod
    def get_activity_timeline(days=7):
        """Get vessel activity over time"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Get position updates per day
        daily_activity = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            count = VesselPosition.objects.filter(
                timestamp__gte=day_start,
                timestamp__lt=day_end
            ).count()
            
            daily_activity.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'updates': count
            })
        
        return daily_activity
    
    @staticmethod
    def get_notification_analytics():
        """Get notification statistics"""
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()
        
        # Count by type
        type_stats = Notification.objects.values('type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent 7 days
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_count = Notification.objects.filter(
            created_at__gte=seven_days_ago
        ).count()
        
        return {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'read_notifications': total_notifications - unread_notifications,
            'by_type': list(type_stats),
            'recent_7_days': recent_count
        }
    
    @staticmethod
    def get_fleet_overview():
        """Get comprehensive fleet overview"""
        vessels = Vessel.objects.all()
        
        # Age distribution
        current_year = timezone.now().year
        age_distribution = {
            '0-5 years': 0,
            '6-10 years': 0,
            '11-20 years': 0,
            '21+ years': 0,
            'Unknown': 0
        }
        
        for vessel in vessels:
            if vessel.built_year:
                age = current_year - vessel.built_year
                if age <= 5:
                    age_distribution['0-5 years'] += 1
                elif age <= 10:
                    age_distribution['6-10 years'] += 1
                elif age <= 20:
                    age_distribution['11-20 years'] += 1
                else:
                    age_distribution['21+ years'] += 1
            else:
                age_distribution['Unknown'] += 1
        
        # Tonnage statistics
        tonnage_vessels = vessels.exclude(gross_tonnage__isnull=True)
        total_tonnage = sum(v.gross_tonnage or 0 for v in tonnage_vessels)
        avg_tonnage = total_tonnage / tonnage_vessels.count() if tonnage_vessels.count() > 0 else 0
        
        return {
            'age_distribution': [
                {'category': k, 'count': v} for k, v in age_distribution.items()
            ],
            'total_tonnage': total_tonnage,
            'average_tonnage': round(avg_tonnage, 2),
            'total_built_year_known': vessels.exclude(built_year__isnull=True).count()
        }
    
    @staticmethod
    def get_destination_analytics():
        """Get destination statistics"""
        # Count vessels by destination
        destinations = Vessel.objects.exclude(
            destination__isnull=True
        ).exclude(
            destination=''
        ).values('destination').annotate(
            count=Count('id')
        ).order_by('-count')[:10]  # Top 10 destinations
        
        total_with_destination = Vessel.objects.exclude(
            destination__isnull=True
        ).exclude(destination='').count()
        
        total_vessels = Vessel.objects.count()
        without_destination = total_vessels - total_with_destination
        
        return {
            'total_with_destination': total_with_destination,
            'total_without_destination': without_destination,
            'top_destinations': list(destinations)
        }
