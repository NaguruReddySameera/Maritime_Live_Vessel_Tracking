from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.authentication.models import User
from apps.vessels.models import Vessel
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = 'Create sample notifications for testing'

    def handle(self, *args, **kwargs):
        # Get all users
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return

        # Get some vessels
        vessels = list(Vessel.objects.all()[:10])
        if not vessels:
            self.stdout.write(self.style.ERROR('No vessels found. Please add vessels first.'))
            return

        # Sample notifications data
        notifications_data = [
            {
                'type': 'alert',
                'title': 'Speed Alert',
                'message': f'{vessels[0].vessel_name} exceeded speed limit in restricted zone',
                'vessel': vessels[0],
                'minutes_ago': 15,
            },
            {
                'type': 'warning',
                'title': 'Course Deviation',
                'message': f'{vessels[1].vessel_name} deviated from planned route',
                'vessel': vessels[1],
                'minutes_ago': 45,
            },
            {
                'type': 'info',
                'title': 'Position Update',
                'message': f'{vessels[2].vessel_name} updated position',
                'vessel': vessels[2],
                'minutes_ago': 120,
                'is_read': True,
            },
            {
                'type': 'success',
                'title': 'Port Arrival',
                'message': f'{vessels[3].vessel_name} arrived at destination port',
                'vessel': vessels[3],
                'minutes_ago': 180,
                'is_read': True,
            },
            {
                'type': 'alert',
                'title': 'Weather Alert',
                'message': f'{vessels[4].vessel_name} approaching storm area',
                'vessel': vessels[4],
                'minutes_ago': 30,
            },
            {
                'type': 'info',
                'title': 'Maintenance Due',
                'message': f'{vessels[5].vessel_name} scheduled maintenance in 7 days',
                'vessel': vessels[5],
                'minutes_ago': 240,
                'is_read': True,
            },
        ]

        created_count = 0
        for user in users:
            for notif_template in notifications_data:
                # Create a copy of the template for each user
                notif_data = notif_template.copy()
                minutes_ago = notif_data.pop('minutes_ago')
                is_read = notif_data.pop('is_read', False)
                
                created_at = timezone.now() - timedelta(minutes=minutes_ago)
                
                notification = Notification.objects.create(
                    user=user,
                    created_at=created_at,
                    is_read=is_read,
                    read_at=created_at + timedelta(minutes=5) if is_read else None,
                    **notif_data
                )
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} notifications for {users.count()} user(s)'
            )
        )
