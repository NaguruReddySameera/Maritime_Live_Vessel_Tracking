# Vessel Tracking API Endpoints

## Overview
Complete REST API for vessel tracking, position management, notes, and route planning.

## Base URL
```
http://localhost:8000/api/
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

---

## Vessel Endpoints

### 1. List Vessels
```http
GET /api/vessels/
```

**Query Parameters:**
- `query` - Search by name, MMSI, or IMO
- `vessel_type` - Filter by type (cargo, tanker, passenger, fishing, etc.)
- `status` - Filter by status (underway, at_anchor, moored, etc.)
- `flag_country` - Filter by flag country (2-letter code)
- `is_tracked` - Filter tracked vessels (true/false)
- `min_speed`, `max_speed` - Speed range filter
- `min_lat`, `max_lat`, `min_lon`, `max_lon` - Bounding box filter
- `search` - Full-text search
- `ordering` - Sort by field (vessel_name, last_position_update, etc.)
- `page` - Page number (pagination)

**Permissions:** Operator, Analyst, Admin

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "mmsi": "123456789",
      "imo_number": "9876543",
      "vessel_name": "Atlantic Explorer",
      "vessel_type": "cargo",
      "flag_country": "US",
      "status": "underway",
      "current_coordinates": [40.7128, -74.0060],
      "speed_over_ground": "15.50",
      "destination": "Port of Singapore",
      "eta": "2025-12-15T10:00:00Z",
      "last_position_update": "2025-12-06T12:00:00Z",
      "is_tracked": true,
      "distance_from_destination": null
    }
  ]
}
```

### 2. Get Vessel Details
```http
GET /api/vessels/{id}/
```

**Permissions:** Operator, Analyst, Admin

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "mmsi": "123456789",
    "imo_number": "9876543",
    "vessel_name": "Atlantic Explorer",
    "call_sign": "WXY123",
    "vessel_type": "cargo",
    "flag_country": "US",
    "built_year": 2015,
    "gross_tonnage": 50000,
    "deadweight": 45000,
    "length_overall": "200.00",
    "beam": "32.00",
    "draft": "12.50",
    "status": "underway",
    "current_coordinates": [40.7128, -74.0060],
    "latitude": "40.7128000",
    "longitude": "-74.0060000",
    "speed_over_ground": "15.50",
    "course_over_ground": "180.00",
    "heading": 175,
    "destination": "Port of Singapore",
    "eta": "2025-12-15T10:00:00Z",
    "last_position_update": "2025-12-06T12:00:00Z",
    "data_source": "ais",
    "ais_update_frequency": 60,
    "is_tracked": true,
    "notes": "Container ship on scheduled route",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-12-06T12:00:00Z",
    "recent_positions": [...],
    "notes_count": 5,
    "active_route": {...}
  }
}
```

### 3. Create Vessel
```http
POST /api/vessels/
```

**Permissions:** Admin only

**Request Body:**
```json
{
  "mmsi": "123456789",
  "imo_number": "9876543",
  "vessel_name": "Atlantic Explorer",
  "call_sign": "WXY123",
  "vessel_type": "cargo",
  "flag_country": "US",
  "built_year": 2015,
  "gross_tonnage": 50000,
  "deadweight": 45000,
  "length_overall": 200.00,
  "beam": 32.00,
  "draft": 12.50,
  "status": "underway",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "destination": "Port of Singapore",
  "is_tracked": true
}
```

**Response:** 201 Created with vessel details

### 4. Update Vessel
```http
PUT /api/vessels/{id}/
PATCH /api/vessels/{id}/
```

**Permissions:** Admin only

**Request Body:** Same as create (partial update supported with PATCH)

**Response:** 200 OK with updated vessel details

### 5. Delete Vessel
```http
DELETE /api/vessels/{id}/
```

**Permissions:** Admin only

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Vessel deleted successfully"
  }
}
```

### 6. Get Vessel Track
```http
GET /api/vessels/{id}/track/?start=2025-12-01&end=2025-12-06
```

**Query Parameters:**
- `start` - Start date (ISO 8601 format)
- `end` - End date (ISO 8601 format)

**Permissions:** Operator, Analyst, Admin

**Response:**
```json
{
  "success": true,
  "data": {
    "vessel_id": 1,
    "vessel_name": "Atlantic Explorer",
    "mmsi": "123456789",
    "positions": [
      {
        "id": 100,
        "latitude": "40.7128000",
        "longitude": "-74.0060000",
        "speed_over_ground": "15.50",
        "course_over_ground": "180.00",
        "heading": 175,
        "timestamp": "2025-12-06T12:00:00Z"
      }
    ],
    "start_time": "2025-12-01T00:00:00Z",
    "end_time": "2025-12-06T23:59:59Z",
    "average_speed": "14.75"
  }
}
```

### 7. Update Vessel Position
```http
POST /api/vessels/{id}/update_position/
```

**Permissions:** Admin only

**Request Body:**
```json
{
  "vessel": 1,
  "latitude": 40.7128,
  "longitude": -74.0060,
  "speed_over_ground": 15.5,
  "course_over_ground": 180.0,
  "heading": 175,
  "timestamp": "2025-12-06T12:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Position updated successfully",
    "position": {...}
  }
}
```

### 8. Get Vessel Statistics
```http
GET /api/vessels/{id}/statistics/?days=30
```

**Query Parameters:**
- `days` - Number of days for statistics (default: 30)

**Permissions:** Analyst, Admin

**Response:**
```json
{
  "success": true,
  "data": {
    "vessel_id": 1,
    "vessel_name": "Atlantic Explorer",
    "period_days": 30,
    "average_speed": 14.75,
    "position_updates": 1440
  }
}
```

### 9. Map View (Vessels in Area)
```http
GET /api/vessels/map_view/?min_lat=40&max_lat=41&min_lon=-75&max_lon=-73
```

**Query Parameters:**
- `min_lat`, `max_lat`, `min_lon`, `max_lon` - Bounding box coordinates

**Permissions:** Operator, Analyst, Admin

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 3,
    "vessels": [...]
  }
}
```

### 10. Bulk Update Positions
```http
POST /api/vessels/bulk_update_positions/
```

**Permissions:** Admin only

**Request Body:**
```json
[
  {
    "mmsi": "123456789",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "speed_over_ground": 15.5,
    "timestamp": "2025-12-06T12:00:00Z"
  }
]
```

**Response:**
```json
{
  "success": true,
  "data": {
    "updated": 1,
    "errors": []
  }
}
```

### 11. Fleet Statistics
```http
GET /api/vessels/fleet_statistics/
```

**Permissions:** Analyst, Admin

**Response:**
```json
{
  "success": true,
  "data": {
    "total_vessels": 150,
    "tracked_vessels": 120,
    "by_type": [
      {"vessel_type": "cargo", "count": 50},
      {"vessel_type": "tanker", "count": 30}
    ],
    "by_status": [
      {"status": "underway", "count": 80},
      {"status": "at_anchor", "count": 40}
    ]
  }
}
```

---

## Vessel Position Endpoints

### 1. List Positions
```http
GET /api/positions/
```

**Query Parameters:**
- `vessel` - Filter by vessel ID
- `mmsi` - Filter by MMSI
- `start` - Start datetime
- `end` - End datetime
- `data_source` - Filter by source (ais, manual, mock)

**Permissions:** Operator, Analyst, Admin

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 100,
      "vessel": 1,
      "vessel_name": "Atlantic Explorer",
      "coordinates": [40.7128, -74.0060],
      "latitude": "40.7128000",
      "longitude": "-74.0060000",
      "speed_over_ground": "15.50",
      "course_over_ground": "180.00",
      "heading": 175,
      "navigational_status": "underway",
      "timestamp": "2025-12-06T12:00:00Z",
      "received_at": "2025-12-06T12:00:05Z",
      "data_source": "ais"
    }
  ]
}
```

---

## Vessel Note Endpoints

### 1. List Notes
```http
GET /api/notes/
```

**Query Parameters:**
- `vessel_id` - Filter by vessel
- `user` - Filter by user
- `is_important` - Filter important notes

**Permissions:** Operator, Analyst, Admin

### 2. Create Note
```http
POST /api/notes/
```

**Request Body:**
```json
{
  "vessel": 1,
  "title": "Engine Maintenance Required",
  "content": "Vessel requires scheduled maintenance at next port",
  "is_important": true
}
```

**Permissions:** Operator, Analyst, Admin

**Response:** 201 Created with note details

### 3. Update/Delete Note
```http
PUT /api/notes/{id}/
DELETE /api/notes/{id}/
```

**Permissions:** Note creator or Admin

---

## Vessel Route Endpoints

### 1. List Routes
```http
GET /api/routes/
```

**Query Parameters:**
- `vessel_id` - Filter by vessel
- `is_active` - Filter active routes
- `created_by` - Filter by creator

**Permissions:** Analyst, Admin

### 2. Create Route
```http
POST /api/routes/
```

**Request Body:**
```json
{
  "vessel": 1,
  "route_name": "Singapore to Rotterdam",
  "origin": "Singapore",
  "destination": "Rotterdam",
  "waypoints": [
    [1.3521, 103.8198],
    [15.0, 50.0],
    [51.9225, 4.4792]
  ],
  "planned_departure": "2025-12-10T00:00:00Z",
  "planned_arrival": "2025-12-25T00:00:00Z",
  "estimated_distance_nm": 8500.00,
  "notes": "Standard route via Suez Canal"
}
```

**Permissions:** Analyst, Admin

**Response:** 201 Created with route details

### 3. Activate Route
```http
POST /api/routes/{id}/activate/
```

**Permissions:** Analyst, Admin

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Route activated successfully",
    "route": {...}
  }
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "success": false,
  "error": {
    "message": "Error description",
    "details": {...}
  }
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing or invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

---

## Permission Matrix

| Endpoint | Operator | Analyst | Admin |
|----------|----------|---------|-------|
| List Vessels | ✅ | ✅ | ✅ |
| Get Vessel Details | ✅ | ✅ | ✅ |
| Create Vessel | ❌ | ❌ | ✅ |
| Update Vessel | ❌ | ❌ | ✅ |
| Delete Vessel | ❌ | ❌ | ✅ |
| Get Track | ✅ | ✅ | ✅ |
| Update Position | ❌ | ❌ | ✅ |
| Vessel Statistics | ❌ | ✅ | ✅ |
| Map View | ✅ | ✅ | ✅ |
| Fleet Statistics | ❌ | ✅ | ✅ |
| List Positions | ✅ | ✅ | ✅ |
| Create Note | ✅ | ✅ | ✅ |
| Update/Delete Note | ✅ (own) | ✅ (own) | ✅ (all) |
| List Routes | ❌ | ✅ | ✅ |
| Create Route | ❌ | ✅ | ✅ |
| Activate Route | ❌ | ✅ | ✅ |

---

## Pagination

List endpoints support pagination. Response includes:

```json
{
  "success": true,
  "count": 150,
  "next": "http://localhost:8000/api/vessels/?page=2",
  "previous": null,
  "data": [...]
}
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 50, max: 100)
