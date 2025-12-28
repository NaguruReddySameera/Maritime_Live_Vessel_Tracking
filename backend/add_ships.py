#!/usr/bin/env python3
import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django
sys.path.append('/home/mastan/Music/Live_tracking/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maritime_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.vessels.models import Vessel, VesselPosition

User = get_user_model()

# Get admin user for owner
admin = User.objects.filter(role='admin').first()

# Ship data with global locations
ships_data = [
    # North Atlantic
    {"name": "Atlantic Explorer", "type": "cargo", "status": "underway", "lat": 45.5, "lon": -30.2},
    {"name": "Ocean Pioneer", "type": "tanker", "status": "at_anchor", "lat": 40.7, "lon": -25.3},
    {"name": "Sea Wanderer", "type": "passenger", "status": "moored", "lat": 51.5, "lon": -0.1},
    
    # Mediterranean
    {"name": "Mediterranean Star", "type": "cargo", "status": "underway", "lat": 36.5, "lon": 14.5},
    {"name": "Aegean Dream", "type": "passenger", "status": "moored", "lat": 37.9, "lon": 23.7},
    {"name": "Malta Trader", "type": "cargo", "status": "at_anchor", "lat": 35.9, "lon": 14.5},
    
    # Indian Ocean
    {"name": "Mumbai Express", "type": "cargo", "status": "underway", "lat": 18.9, "lon": 72.8},
    {"name": "Arabian Gulf", "type": "tanker", "status": "underway", "lat": 25.2, "lon": 55.3},
    {"name": "Maldives Cruiser", "type": "passenger", "status": "moored", "lat": 4.1, "lon": 73.5},
    
    # Pacific Ocean
    {"name": "Pacific Navigator", "type": "cargo", "status": "underway", "lat": 35.7, "lon": 139.7},
    {"name": "Sydney Trader", "type": "cargo", "status": "at_anchor", "lat": -33.9, "lon": 151.2},
    {"name": "Hawaii Dream", "type": "passenger", "status": "moored", "lat": 21.3, "lon": -157.8},
    
    # South China Sea
    {"name": "Singapore Express", "type": "cargo", "status": "underway", "lat": 1.3, "lon": 103.8},
    {"name": "Manila Bay", "type": "tanker", "status": "moored", "lat": 14.6, "lon": 120.9},
    {"name": "Hong Kong Trader", "type": "cargo", "status": "underway", "lat": 22.3, "lon": 114.2},
    
    # Caribbean
    {"name": "Caribbean Queen", "type": "passenger", "status": "moored", "lat": 18.4, "lon": -66.1},
    {"name": "Bahamas Runner", "type": "cargo", "status": "underway", "lat": 25.0, "lon": -77.4},
    {"name": "Jamaica Star", "type": "tanker", "status": "at_anchor", "lat": 17.9, "lon": -76.8},
    
    # North Sea
    {"name": "North Sea Viking", "type": "fishing", "status": "underway", "lat": 57.0, "lon": 2.0},
    {"name": "Rotterdam Express", "type": "cargo", "status": "moored", "lat": 51.9, "lon": 4.5},
    {"name": "Oslo Trader", "type": "cargo", "status": "at_anchor", "lat": 59.9, "lon": 10.7},
    
    # Red Sea
    {"name": "Suez Passage", "type": "tanker", "status": "underway", "lat": 29.9, "lon": 32.5},
    {"name": "Red Sea Trader", "type": "cargo", "status": "underway", "lat": 20.0, "lon": 38.5},
    
    # South Atlantic
    {"name": "Cape Town Express", "type": "cargo", "status": "moored", "lat": -33.9, "lon": 18.4},
    {"name": "Rio Grande", "type": "tanker", "status": "underway", "lat": -22.9, "lon": -43.2},
    {"name": "Buenos Aires Trader", "type": "cargo", "status": "at_anchor", "lat": -34.6, "lon": -58.4},
    
    # Additional vessels
    {"name": "Arctic Explorer", "type": "fishing", "status": "underway", "lat": 70.0, "lon": 25.0},
    {"name": "Persian Gulf Tanker", "type": "tanker", "status": "moored", "lat": 26.0, "lon": 50.5},
    {"name": "Black Sea Navigator", "type": "cargo", "status": "underway", "lat": 44.0, "lon": 33.0},
    {"name": "Baltic Trader", "type": "cargo", "status": "at_anchor", "lat": 59.4, "lon": 24.7},
]

# Additional random statuses
all_statuses = ['underway', 'at_anchor', 'moored', 'not_under_command', 'restricted_maneuverability']
destinations = ['New York', 'London', 'Singapore', 'Rotterdam', 'Shanghai', 'Dubai', 'Hamburg', 'Los Angeles', 'Tokyo', 'Mumbai']

print(f"Adding {len(ships_data)} vessels...")

for idx, ship in enumerate(ships_data, 1):
    mmsi = 200000000 + idx
    imo = 9000000 + idx
    
    # Random status distribution
    status = ship['status']
    
    # Create vessel
    vessel = Vessel.objects.create(
        vessel_name=ship['name'],
        mmsi=mmsi,
        imo_number=str(imo),
        call_sign=f"CALL{idx:03d}",
        vessel_type=ship['type'],
        flag_country=random.choice(['US', 'UK', 'CN', 'SG', 'NL', 'NO', 'JP', 'KR']),
        status=status,
        latitude=ship['lat'],
        longitude=ship['lon'],
        speed_over_ground=round(random.uniform(0, 25), 1) if status == 'underway' else 0.0,
        course_over_ground=random.randint(0, 359) if status == 'underway' else 0,
        destination=random.choice(destinations) if status == 'underway' else None,
        eta=datetime.now() + timedelta(days=random.randint(1, 10)) if status == 'underway' else None,
        draft=round(random.uniform(5.0, 15.0), 1),
        length_overall=round(random.uniform(100, 350), 1),
        beam=round(random.uniform(15, 50), 1),
        is_tracked=True,
        last_position_update=datetime.now()
    )
    
    # Create initial position
    VesselPosition.objects.create(
        vessel=vessel,
        latitude=ship['lat'],
        longitude=ship['lon'],
        speed_over_ground=vessel.speed_over_ground,
        course_over_ground=vessel.course_over_ground,
        heading=vessel.course_over_ground,
        timestamp=datetime.now() - timedelta(minutes=random.randint(1, 30))
    )
    
    # Add a few historical positions for underway vessels
    if status == 'underway':
        for i in range(1, 4):
            lat_offset = random.uniform(-0.5, 0.5)
            lon_offset = random.uniform(-0.5, 0.5)
            VesselPosition.objects.create(
                vessel=vessel,
                latitude=ship['lat'] + lat_offset,
                longitude=ship['lon'] + lon_offset,
                speed_over_ground=round(random.uniform(10, 20), 1),
                course_over_ground=random.randint(0, 359),
                heading=random.randint(0, 359),
                timestamp=datetime.now() - timedelta(hours=i*2)
            )
    
    print(f"  ✓ {ship['name']} ({ship['type']}) - {status} at ({ship['lat']}, {ship['lon']})")

print(f"\nSuccessfully added {len(ships_data)} vessels!")
print(f"Total vessels in database: {Vessel.objects.filter(is_deleted=False).count()}")

# Show status distribution
from django.db.models import Count
status_counts = Vessel.objects.filter(is_deleted=False).values('status').annotate(count=Count('id'))
print("\nStatus distribution:")
for item in status_counts:
    print(f"  {item['status']}: {item['count']}")
