# API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

### Get Token
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "success": true,
  "token": "eyJhbGc...",
  "refreshToken": "eyJhbGc...",
  "user": {
    "id": "...",
    "email": "user@example.com",
    "role": "operator",
    ...
  }
}
```

---

## Authentication Endpoints

### POST `/auth/register` (Admin only)
Create new user account

**Request:**
```json
{
  "email": "newuser@example.com",
  "password": "SecurePass@123",
  "firstName": "John",
  "lastName": "Doe",
  "company": "Shipping Co",
  "organizationType": "shipping_company",
  "role": "operator"
}
```

### POST `/auth/login`
User login

### POST `/auth/logout`
Logout current user

### POST `/auth/refresh`
Refresh JWT token
```json
{
  "refreshToken": "..."
}
```

### GET `/auth/profile`
Get current user profile

### PUT `/auth/profile`
Update own profile

---

## User Management (Admin Only)

### GET `/users`
List all users

**Query Parameters:**
- `role` - Filter by role (operator/analyst/admin)
- `company` - Filter by company
- `isActive` - Filter by active status (true/false)
- `search` - Search by name or email
- `page` - Page number (default: 1)
- `limit` - Results per page (default: 20)

### GET `/users/:id`
Get user by ID

### POST `/users`
Create user (same as register)

### PUT `/users/:id`
Update user

### DELETE `/users/:id`
Delete user

### PUT `/users/:id/role`
Change user role
```json
{
  "role": "analyst"
}
```

### PUT `/users/:id/lock`
Lock/unlock user account
```json
{
  "isLocked": true
}
```

### POST `/users/:id/reset-password`
Reset user password
```json
{
  "password": "NewPass@123"
}
```

---

## Vessel Endpoints

### GET `/vessels`
List vessels with filters

**Query Parameters:**
- `company` - Filter by company name
- `status` - underway, at_anchor, moored, etc.
- `shipType` - cargo, tanker, container, etc.
- `search` - Search by name, IMO, or MMSI
- `minSpeed` / `maxSpeed` - Filter by speed range
- `destination` - Filter by destination port
- `page` / `limit` - Pagination

**Response:**
```json
{
  "success": true,
  "count": 50,
  "totalPages": 3,
  "currentPage": 1,
  "vessels": [...]
}
```

### GET `/vessels/:id`
Get vessel details including operational notes

### GET `/vessels/:id/track` (Analyst+)
Get vessel position history

**Query Parameters:**
- `startDate` - ISO date string
- `endDate` - ISO date string
- `limit` - Max positions to return

### POST `/vessels/:id/notes`
Add operational note
```json
{
  "note": "Delay due to weather conditions"
}
```

### GET `/vessels/:id/notes`
Get all notes for vessel

### GET `/vessels/map/live`
Get live positions for map display

**Query Parameters:**
- `bounds` - "minLat,minLng,maxLat,maxLng"

---

## Port Endpoints

### GET `/ports`
List ports

**Query Parameters:**
- `region` - Filter by region
- `country` - Filter by country
- `status` - Congestion status (green/yellow/red)
- `search` - Search by name or code

### GET `/ports/:id`
Get port details

### GET `/ports/:id/congestion`
Get current congestion data

### GET `/ports/:id/history` (Analyst+)
Get historical congestion trends

**Query Parameters:**
- `startDate` / `endDate` - Date range
- `interval` - day/week/month

### POST `/ports/:id/congestion` (Admin)
Update port congestion status
```json
{
  "status": "yellow",
  "vesselsWaiting": 10,
  "averageWaitTime": 6.5
}
```

### GET `/ports/analytics/compare` (Analyst+)
Compare multiple ports

**Query Parameters:**
- `portIds` - Comma-separated port IDs
- `startDate` / `endDate` - Date range

---

## Safety Endpoints

### GET `/safety/piracy`
Get active piracy zones

### GET `/safety/weather`
Get weather warnings and storm zones

### GET `/safety/incidents`
Get accident hotspots

**Query Parameters:**
- `startDate` / `endDate` - Date range
- `severity` - low/medium/high/critical

### GET `/safety/zones`
Get safety zones near location

**Query Parameters:**
- `latitude` / `longitude` - Required
- `radius` - Radius in nautical miles (default: 100)

### GET `/safety/alerts`
Get active alerts for current user

**Query Parameters:**
- `type` - piracy/weather/congestion/safety/operational
- `severity` - info/warning/critical
- `status` - active/resolved/expired (default: active)

### POST `/safety/zones` (Admin)
Create safety zone
```json
{
  "type": "piracy",
  "severity": "high",
  "title": "High Risk Area",
  "description": "Piracy incidents reported",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[...]]
  }
}
```

### GET `/safety/analytics/risks` (Analyst+)
Get risk analytics

---

## Analytics Endpoints (Analyst+)

### GET `/analytics/voyages`
Get voyage analytics

**Query Parameters:**
- `startDate` / `endDate` - Date range
- `vesselId` - Filter by vessel
- `company` - Filter by company

**Response includes:**
- Duration
- Distance traveled
- Average speed
- Position count

### GET `/analytics/routes`
Get route optimization data

**Query Parameters:**
- `origin` / `destination` - Port names
- `startDate` / `endDate` - Date range

### GET `/analytics/risks`
Get risk assessments for vessels

**Query Parameters:**
- `vesselId` - Specific vessel
- `region` - Geographic region
- `riskType` - Type of risk to analyze

### POST `/analytics/export`
Export data to CSV/Excel
```json
{
  "dataType": "vessels",
  "filters": {...},
  "format": "csv"
}
```

---

## Dashboard Endpoints

### GET `/dashboards`
Get user's dashboards

### GET `/dashboards/:id`
Get dashboard by ID

### POST `/dashboards` (Analyst+)
Create dashboard
```json
{
  "name": "Fleet Overview",
  "description": "Main fleet dashboard",
  "layout": [
    {
      "widgetType": "map",
      "position": { "x": 0, "y": 0, "width": 6, "height": 4 },
      "config": {
        "title": "Live Fleet Map",
        "dataSource": "vessels",
        "refreshInterval": 30000
      }
    }
  ]
}
```

### PUT `/dashboards/:id` (Analyst+)
Update dashboard

### DELETE `/dashboards/:id`
Delete dashboard (owner only)

### POST `/dashboards/:id/share` (Analyst+)
Share dashboard with user
```json
{
  "userId": "user_id",
  "permission": "view"
}
```

---

## Admin Endpoints (Admin Only)

### GET `/admin/health`
Get system health status

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "database": {
    "status": "connected",
    "collections": {
      "users": 10,
      "vessels": 50,
      "ports": 25
    }
  },
  "system": {
    "uptime": 3600,
    "memory": {...},
    "cpu": {...}
  }
}
```

### GET `/admin/logs`
Get system logs

**Query Parameters:**
- `level` - info/warn/error
- `startDate` / `endDate`
- `page` / `limit`

### GET `/admin/audit`
Get audit trail

**Query Parameters:**
- `userId` - Filter by user
- `resource` - Filter by resource type
- `action` - Filter by action
- `startDate` / `endDate`

### GET `/admin/sources`
Get external data sources configuration

### POST `/admin/sources/sync`
Trigger manual data sync
```json
{
  "sourceType": "ais"
}
```

### GET `/admin/config`
Get system configuration

### PUT `/admin/config`
Update system configuration
```json
{
  "category": "security",
  "settings": {
    "maxLoginAttempts": 5,
    "sessionTimeout": 3600
  }
}
```

### GET `/admin/stats`
Get system statistics and metrics

---

## Error Responses

All error responses follow this format:

```json
{
  "message": "Error description",
  "errors": ["Detailed error 1", "Detailed error 2"]
}
```

**Common Status Codes:**
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `423` - Locked (account locked)
- `500` - Internal Server Error

---

## Rate Limiting

- **Rate:** 100 requests per 15 minutes per IP
- **Response when exceeded:**
```json
{
  "message": "Too many requests, please try again later"
}
```

---

## WebSocket Events

Connect to Socket.IO at `http://localhost:5000`

### Client → Server

```javascript
// Subscribe to vessel updates
socket.emit('subscribe:vessels');

// Subscribe to port updates
socket.emit('subscribe:port', portId);
```

### Server → Client

```javascript
// Vessel position updated
socket.on('vessel:position:updated', (data) => {
  // data: { vesselId, position }
});

// Port congestion updated
socket.on('port:congestion:updated', (data) => {
  // data: { portId, congestion }
});

// New alert created
socket.on('alert:created', (alert) => {
  // alert: Alert object
});
```
