"""
Celery configuration for Maritime Project
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maritime_project.settings')

app = Celery('maritime_project')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Update vessel positions every 60 seconds
    'update-vessel-positions': {
        'task': 'apps.vessels.tasks.update_vessel_positions',
        'schedule': 60.0,  # Every 60 seconds
    },
    # Check for stale vessel tracking every 6 hours
    'check-vessel-tracking-status': {
        'task': 'apps.vessels.tasks.check_vessel_tracking_status',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    # Clean up old vessel positions daily
    'cleanup-old-positions': {
        'task': 'apps.vessels.tasks.cleanup_old_positions',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1:00 AM
    },
    # Clean up old audit logs daily
    'cleanup-audit-logs': {
        'task': 'apps.authentication.tasks.cleanup_old_audit_logs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2:00 AM
    },
    # Clean up inactive sessions daily
    'cleanup-inactive-sessions': {
        'task': 'apps.authentication.tasks.cleanup_inactive_sessions',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3:00 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
