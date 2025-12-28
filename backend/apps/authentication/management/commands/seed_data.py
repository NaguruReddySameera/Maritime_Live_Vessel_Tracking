"""
Django management command to seed initial data
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.vessels.models import Vessel, VesselPosition
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with initial test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')
        
        # Create users
        self.stdout.write('Creating users...')
        users = self.create_users()
        
        # Create vessels
        self.stdout.write('Creating vessels...')
        vessels = self.create_vessels()
        
        # Create vessel positions
        self.stdout.write('Creating vessel positions...')
        self.create_vessel_positions(vessels)
        
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write(f'Created {len(users)} users, {len(vessels)} vessels')
        self.stdout.write('\n=== Test User Credentials ===')
        self.stdout.write('Admin: sameerareddy583@gmail.com / admin')
        self.stdout.write('Analyst: analyst@maritimetracking.com / Analyst@123')
        self.stdout.write('Operator: operator@maritimetracking.com / Operator@123')

    def create_users(self):
        """Create test users"""
        users = []
        
        # Admin user
        if not User.objects.filter(email='sameerareddy583@gmail.com').exists():
            admin = User.objects.create_user(
                email='sameerareddy583@gmail.com',
                password='admin',
                first_name='Admin',
                last_name='User',
                role='admin',
                organization='Maritime Corp',
                department='IT',
                position='System Administrator',
                is_verified=True,
                is_staff=True,
                is_superuser=True
            )
            users.append(admin)
            self.stdout.write(f'  ✓ Created admin: {admin.email}')
        
        # Analyst user
        if not User.objects.filter(email='analyst@maritimetracking.com').exists():
            analyst = User.objects.create_user(
                email='analyst@maritimetracking.com',
                password='Analyst@123',
                first_name='Sarah',
                last_name='Johnson',
                role='analyst',
                organization='Maritime Corp',
                department='Analytics',
                position='Senior Analyst',
                is_verified=True
            )
            users.append(analyst)
            self.stdout.write(f'  ✓ Created analyst: {analyst.email}')
        
        # Operator user
        if not User.objects.filter(email='operator@maritimetracking.com').exists():
            operator = User.objects.create_user(
                email='operator@maritimetracking.com',
                password='Operator@123',
                first_name='John',
                last_name='Smith',
                role='operator',
                organization='Maritime Corp',
                department='Operations',
                position='Operations Manager',
                is_verified=True
            )
            users.append(operator)
            self.stdout.write(f'  ✓ Created operator: {operator.email}')
        
        return users

    def create_vessels(self):
        """Create test vessels"""
        vessels_data = [
            {
                'mmsi': '123456789',
                'imo_number': '9876543',
                'vessel_name': 'Atlantic Explorer',
                'vessel_type': 'cargo',
                'flag_country': 'US',
                'built_year': 2015,
                'gross_tonnage': 50000,
                'latitude': 40.7128,
                'longitude': -74.0060,
                'status': 'underway',
                'speed_over_ground': 15.5,
                'course_over_ground': 180.0,
                'destination': 'Port of Singapore',
            },
            {
                'mmsi': '987654321',
                'imo_number': '1234567',
                'vessel_name': 'Pacific Pride',
                'vessel_type': 'tanker',
                'flag_country': 'GB',
                'built_year': 2018,
                'gross_tonnage': 75000,
                'latitude': 1.3521,
                'longitude': 103.8198,
                'status': 'moored',
                'speed_over_ground': 0.0,
                'course_over_ground': 0.0,
                'destination': 'Port of Rotterdam',
            },
            {
                'mmsi': '456789123',
                'imo_number': '7654321',
                'vessel_name': 'Caribbean Queen',
                'vessel_type': 'passenger',
                'flag_country': 'PA',
                'built_year': 2020,
                'gross_tonnage': 100000,
                'latitude': 25.7617,
                'longitude': -80.1918,
                'status': 'at_anchor',
                'speed_over_ground': 0.5,
                'course_over_ground': 45.0,
                'destination': 'Miami Port',
            },
        ]
        
        vessels = []
        for data in vessels_data:
            vessel, created = Vessel.objects.get_or_create(
                mmsi=data['mmsi'],
                defaults={
                    **data,
                    'last_position_update': timezone.now(),
                    'data_source': 'seed',
                }
            )
            if created:
                vessels.append(vessel)
                self.stdout.write(f'  ✓ Created vessel: {vessel.vessel_name}')
        
        return vessels

    def create_vessel_positions(self, vessels):
        """Create historical positions for vessels"""
        for vessel in vessels:
            # Create 10 historical positions
            base_lat = float(vessel.latitude)
            base_lon = float(vessel.longitude)
            
            for i in range(10):
                # Simulate movement
                lat_offset = random.uniform(-0.1, 0.1)
                lon_offset = random.uniform(-0.1, 0.1)
                
                VesselPosition.objects.create(
                    vessel=vessel,
                    latitude=base_lat + lat_offset,
                    longitude=base_lon + lon_offset,
                    speed_over_ground=random.uniform(0, 20),
                    course_over_ground=random.uniform(0, 360),
                    heading=random.randint(0, 359),
                    navigational_status=vessel.status,
                    timestamp=timezone.now() - timezone.timedelta(hours=i),
                    data_source='seed'
                )
            
            self.stdout.write(f'  ✓ Created 10 positions for {vessel.vessel_name}')
