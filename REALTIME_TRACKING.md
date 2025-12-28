# Real-Time Vessel Tracking

## Overview

This application now supports **FREE real-time vessel tracking** using live AIS (Automatic Identification System) data from multiple sources.

## Data Sources

### 1. AISHub (PRIMARY - FREE)
- **Website**: http://www.aishub.net/
- **Cost**: FREE (using demo access)
- **Coverage**: Global vessel tracking
- **Update Frequency**: Real-time updates
- **API Endpoint**: `http://data.aishub.net/ws.php`
- **No API Key Required**: Uses `AH_DEMO` username for free access

### 2. MarineTraffic (FALLBACK - Paid)
- **Website**: https://www.marinetraffic.com/
- **Cost**: Paid API key required
- **Coverage**: Global, more comprehensive
- **Only used if**: AISHub data is unavailable

## Features

### 1. Real-Time Position Updates
- Live vessel positions updated from AIS data
- Shows actual ship movements on the map
- Includes speed, course, heading, and status
- Updates can be automatic or manual

### 2. Area-Based Tracking
- Fetch all vessels in a specific geographic area
- Supports bounding box queries (min/max lat/lon)
- Efficient for map view implementations

### 3. Individual Vessel Updates
- Update any vessel's position from live AIS data
- Requires vessel to have MMSI number
- Creates position history for tracking

## API Endpoints

### Get Real-Time Positions in Area
```bash
GET /api/vessels/realtime_positions/
```

**Query Parameters:**
- `min_lat`: Minimum latitude (default: -90)
- `max_lat`: Maximum latitude (default: 90)
- `min_lon`: Minimum longitude (default: -180)
- `max_lon`: Maximum longitude (default: 180)

**Example:**
```bash
curl -X GET "http://localhost:8000/api/vessels/realtime_positions/?min_lat=30&max_lat=50&min_lon=-10&max_lon=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "vessels": [
      {
        "mmsi": "219000606",
        "name": "OPAL QUEEN",
        "latitude": 55.567,
        "longitude": 12.345,
        "speed": 12.3,
        "course": 245.0,
        "heading": 244,
        "status": "underway",
        "vessel_type": "Cargo",
        "destination": "ROTTERDAM",
        "eta": "12-18 14:00",
        "timestamp": "2025-12-18T10:30:45Z",
        "source": "aishub"
      }
    ],
    "count": 150,
    "source": "aishub_free",
    "timestamp": "2025-12-18T10:30:45.123456Z"
  }
}
```

### Update Vessel from AIS
```bash
POST /api/vessels/{id}/update_from_ais/
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/vessels/123/update_from_ais/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "vessel": {
      "id": 123,
      "mmsi": "219000606",
      "vessel_name": "OPAL QUEEN",
      "latitude": "55.567000",
      "longitude": "12.345000",
      "speed_over_ground": "12.3",
      "course_over_ground": "245.0",
      "heading": 244,
      "last_position_update": "2025-12-18T10:30:45Z",
      "data_source": "aishub"
    },
    "message": "Vessel position updated from aishub"
  }
}
```

## Frontend Integration

### Using vesselService

```typescript
import vesselService from './services/vesselService';

// Get real-time positions in a specific area
const realtimeData = await vesselService.getRealtimePositions(
  30,  // min_lat
  50,  // max_lat
  -10, // min_lon
  10   // max_lon
);

console.log(`Found ${realtimeData.count} vessels`);
console.log(`Data source: ${realtimeData.source}`);
realtimeData.vessels.forEach(vessel => {
  console.log(`${vessel.name} at (${vessel.latitude}, ${vessel.longitude})`);
});

// Update a specific vessel from AIS
const updatedVessel = await vesselService.updateFromAIS(vesselId);
console.log(`Updated: ${updatedVessel.vessel_name}`);
```

### Auto-Refresh Implementation

```typescript
// Refresh vessel positions every 30 seconds
const REFRESH_INTERVAL = 30000; // 30 seconds

useEffect(() => {
  const fetchRealtime = async () => {
    try {
      const data = await vesselService.getRealtimePositions(
        mapBounds.minLat,
        mapBounds.maxLat,
        mapBounds.minLon,
        mapBounds.maxLon
      );
      setVessels(data.vessels);
    } catch (error) {
      console.error('Failed to fetch real-time data:', error);
    }
  };

  fetchRealtime(); // Initial load
  
  const interval = setInterval(fetchRealtime, REFRESH_INTERVAL);
  
  return () => clearInterval(interval);
}, [mapBounds]);
```

## Backend Implementation

### Service Layer (`apps/vessels/services.py`)

The `AISIntegrationService` class handles all AIS data integration:

```python
class AISIntegrationService:
    def __init__(self):
        self.aishub_url = 'http://data.aishub.net/ws.php'
    
    def fetch_vessel_position(self, mmsi):
        """Fetch position for a single vessel by MMSI"""
        # Tries AISHub first (free), falls back to MarineTraffic
        
    def fetch_vessels_in_area(self, min_lat, max_lat, min_lon, max_lon):
        """Fetch all vessels in a geographic area"""
        # Uses AISHub free API
```

### Views (`apps/vessels/views.py`)

New endpoints added:
- `realtime_positions`: Get all vessels in an area
- `update_from_ais`: Update a specific vessel from AIS

## Data Fields

### Vessel Data from AIS
- **MMSI**: Maritime Mobile Service Identity (unique ID)
- **Name**: Vessel name
- **Position**: Latitude/Longitude in decimal degrees
- **Speed**: Speed over ground in knots
- **Course**: Course over ground in degrees (0-360)
- **Heading**: True heading in degrees (0-359)
- **Status**: Navigation status (underway, anchored, moored, etc.)
- **Type**: Vessel type (cargo, tanker, passenger, etc.)
- **Destination**: Port of destination
- **ETA**: Estimated time of arrival
- **Timestamp**: Time of last position update

## Configuration

### No Configuration Required for Free Access

The system uses AISHub's demo access by default:
- Username: `AH_DEMO`
- No API key needed
- Global coverage
- Real-time updates

### Optional: MarineTraffic API Key

For enhanced data quality, add to `.env`:
```bash
MARINETRAFFIC_API_KEY=your_api_key_here
```

### Optional: MarineSia API Key (Recommended)

MarineSia provides free vessel lookups and area queries. To enable it in the Django backend, add to `backend/.env`:
```bash
MARINESIA_API_KEY=rwcxgUmACAeJJCshUZAbtoOzC
```

Once set, the backend will prioritize MarineSia for `realtime_positions` and `update_from_ais` endpoints, falling back to AISHub when needed.

## Usage Examples

### 1. Map View with Real-Time Updates
- Display vessels on an interactive map
- Auto-refresh every 30-60 seconds
- Click vessels for detailed information

### 2. Fleet Tracking Dashboard
- Monitor multiple vessels in real-time
- Display status, speed, and heading
- Track vessels entering/leaving zones

### 3. Alert System
- Detect vessels entering restricted areas
- Monitor speed violations
- Track off-course navigation

## Performance Notes

### AISHub Free Tier Limits
- **Rate Limiting**: Reasonable request frequency
- **Coverage**: Global but may have gaps in remote areas
- **Update Rate**: Typically 1-5 minute updates per vessel
- **Concurrent Requests**: Keep requests moderate

### Optimization Tips
1. **Cache Results**: Cache positions for 30-60 seconds
2. **Limit Area**: Query only visible map area
3. **Batch Updates**: Update multiple vessels together
4. **Background Jobs**: Use Celery for scheduled updates

## Testing

### Test Real-Time API
```bash
# Test AISHub direct access
curl "http://data.aishub.net/ws.php?username=AH_DEMO&format=1&output=json&compress=0&latmin=30&latmax=50&lonmin=-10&lonmax=10"

# Test our API endpoint
curl -X GET "http://localhost:8000/api/vessels/realtime_positions/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Sample MMSI Numbers for Testing
- `219000606`: Danish cargo vessel
- `211281960`: German container ship
- `538007462`: US cargo vessel
- `311000719`: Bahamas cruise ship

## Troubleshooting

### No Data Returned
1. Check internet connection
2. Verify AISHub service status: http://www.aishub.net/
3. Try different geographic areas
4. Check vessel has MMSI number

### Slow Response
1. Reduce query area size
2. Increase cache duration
3. Use background tasks for updates

### Inaccurate Positions
1. AIS data may have 1-5 minute delay
2. Vessels in port may not transmit
3. Small vessels may not have AIS

## Future Enhancements

1. **WebSocket Integration**: Push real-time updates to clients
2. **Vessel Prediction**: Predict future positions based on course/speed
3. **Historical Playback**: Replay vessel movements
4. **Advanced Filtering**: Filter by vessel type, flag, size
5. **Multiple AIS Sources**: Integrate more free AIS providers

## Support

For issues or questions:
- Check AISHub documentation: http://www.aishub.net/api
- Review Django logs: `backend/logs/`
- Check browser console for frontend errors

## License

This implementation uses publicly available AIS data from AISHub's free demo service. Commercial use may require proper API subscription.
