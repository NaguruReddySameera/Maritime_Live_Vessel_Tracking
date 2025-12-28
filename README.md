# Maritime Vessel Tracking Platform

## Project Status: In Development

This workspace contains a **Django + Django REST Framework + React.js** maritime vessel tracking platform with comprehensive role-based access control and external API integrations.

## Project Structure

```
Live_tracking/
├── backend/                    # Django + DRF Backend
│   ├── maritime_project/       # Django project configuration
│   ├── apps/                   # Django applications
│   │   ├── authentication/     # ✅ COMPLETE - JWT auth, user management
│   │   ├── vessels/            # ⏳ IN PROGRESS - Vessel tracking
│   │   ├── ports/              # 📋 PLANNED
│   │   ├── safety/             # 📋 PLANNED
│   │   ├── voyages/            # 📋 PLANNED
│   │   ├── notifications/      # 📋 PLANNED
│   │   ├── dashboards/         # 📋 PLANNED
│   │   └── admin_tools/        # 📋 PLANNED
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── README.md
└── frontend/                   # React + TailwindCSS (Planned)
```

## Completed Features ✅

### 1. Authentication System (COMPLETE)
- **Custom User Model** with Operator/Analyst/Admin roles
- **JWT Authentication** with access/refresh tokens
- **Argon2 Password Hashing** for maximum security
- **Account Security:**
  - Failed login attempt tracking
  - Automatic account lockout (5 attempts = 30 min lock)
  - Session tracking with IP and user agent
- **Audit Logging** for all authentication events
- **Endpoints:**
  - `POST /api/auth/login/` - Login with email/password
  - `POST /api/auth/register/` - User registration
  - `POST /api/auth/logout/` - Logout with token blacklisting
  - `POST /api/auth/token/refresh/` - Refresh access token
  - `GET/PUT /api/auth/profile/` - User profile
  - `POST /api/auth/change-password/` - Password change
  - `GET /api/auth/users/` - List users (admin)
  - `GET/PUT/DELETE /api/auth/users/{id}/` - Manage users (admin)

### 2. Core Infrastructure
- **Settings Configuration:**
  - PostgreSQL (production) / SQLite (development)
  - JWT with 1-day access, 7-day refresh
  - CORS configuration
  - Security middleware
- **Base Models:**
  - `TimeStampedModel` - Auto created_at/updated_at
  - `SoftDeleteModel` - Soft delete functionality
- **Error Handling:**
  - Custom exception handler with consistent response format
  - Comprehensive logging
- **Health Checks:**
  - `GET /api/health/` - Basic status
  - `GET /api/health/ready/` - Database + Redis connectivity

### 3. Vessel Models (DATA STRUCTURE ONLY)
- **Vessel** - Ship details, AIS data, current position
- **VesselPosition** - Historical position tracking
- **VesselNote** - User notes on vessels
- **VesselRoute** - Planned/historical routes

## Features Overview

### 🔐 Three-Tier Role System

#### **Operator**
- Live vessel tracking and basic operations
- View vessel metadata and status
- Add operational notes
- Access safety warnings and alerts
- View simple port congestion status

#### **Analyst**
- All Operator capabilities
- Advanced analytics and reporting
- Historical data analysis
- Custom dashboard creation
- Data export capabilities
- Risk assessment and optimization

#### **Admin**
- Full system administration
- User and role management
- System configuration
- API and data source management
- Audit logs and monitoring
- Security policy configuration

### 🚢 Planned Modules

1. **Authentication & Role Management** ✅
   - JWT-based authentication
   - Role-based access control (RBAC)
   - Password policies and security settings

2. **Live Vessel Tracking** ⏳
   - Real-time AIS data integration
   - Interactive map with vessel markers
   - Vessel metadata (IMO, MMSI, cargo, ETA)
   - Filtering and search capabilities

3. **Port Congestion Analytics** 📋
   - Real-time congestion status (Green/Yellow/Red)
   - Historical trends and comparisons
   - Waiting time statistics
   - Multi-port analysis

4. **Safety Overlays**
   - Piracy zones
   - Storm tracking
   - Accident hotspots
   - Weather overlays
   - Automated alerts

5. **Historical Voyage Replay**
   - Time-based voyage playback
   - Route analysis and optimization
   - Incident correlation
   - Audit trail

6. **Multi-Tenant Dashboards**
   - Role-specific views
   - Customizable widgets
   - KPI tracking
   - Scheduled reports

7. **Admin Tools**
   - API health monitoring
   - System logs
   - External source management
   - Configuration management

## Tech Stack

### Backend
- **Node.js** + **Express.js** - REST API
- **MongoDB** - Database
- **Socket.IO** - Real-time updates
- **JWT** - Authentication
- **Winston** - Logging

### Frontend
- **React** - UI framework
- **Leaflet/Mapbox** - Interactive maps
- **Chart.js** - Analytics visualizations
- **Material-UI** - Component library
- **Redux** - State management

## Installation

### Prerequisites
- Node.js 18+ and npm
- MongoDB 6+
- API keys for AIS, Weather, and Piracy data sources

### Setup

1. **Clone and install dependencies:**
```bash
cd Live_tracking
npm install
cd client && npm install && cd ..
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Initialize database:**
```bash
npm run migrate
```

4. **Start development servers:**
```bash
npm run dev:full
```

The API runs on `http://localhost:5000`  
The client runs on `http://localhost:3000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user (Admin only)
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh JWT token
- `PUT /api/auth/profile` - Update own profile

### Users (Admin)
- `GET /api/users` - List all users
- `POST /api/users` - Create user
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user
- `PUT /api/users/:id/role` - Change user role
- `PUT /api/users/:id/lock` - Lock/unlock user

### Vessels
- `GET /api/vessels` - List vessels (with filters)
- `GET /api/vessels/:id` - Get vessel details
- `GET /api/vessels/:id/track` - Get vessel position history
- `POST /api/vessels/:id/notes` - Add operational note

### Port Congestion
- `GET /api/ports` - List ports with congestion status
- `GET /api/ports/:id/congestion` - Detailed congestion data
- `GET /api/ports/:id/history` - Historical congestion trends

### Safety
- `GET /api/safety/piracy` - Piracy zones
- `GET /api/safety/weather` - Weather overlays
- `GET /api/safety/incidents` - Accident hotspots
- `GET /api/safety/alerts` - Active alerts for user's vessels

### Analytics (Analyst+)
- `GET /api/analytics/voyages` - Voyage analytics
- `GET /api/analytics/routes` - Route optimization data
- `GET /api/analytics/risks` - Risk assessments
- `POST /api/analytics/export` - Export data (CSV/Excel)

### Dashboards
- `GET /api/dashboards` - User's dashboards
- `POST /api/dashboards` - Create dashboard
- `PUT /api/dashboards/:id` - Update dashboard
- `DELETE /api/dashboards/:id` - Delete dashboard

### Admin
- `GET /api/admin/health` - System health status
- `GET /api/admin/logs` - System logs
- `GET /api/admin/sources` - External data sources
- `PUT /api/admin/config` - Update system configuration

## Role Permissions Matrix

| Feature | Operator | Analyst | Admin |
|---------|----------|---------|-------|
| View live vessels | ✅ | ✅ | ✅ |
| Add notes | ✅ | ✅ | ✅ |
| Advanced filters | ❌ | ✅ | ✅ |
| Export data | ❌ | ✅ | ✅ |
| Historical analytics | ❌ | ✅ | ✅ |
| Custom dashboards | ❌ | ✅ | ✅ |
| Create users | ❌ | ❌ | ✅ |
| Manage roles | ❌ | ❌ | ✅ |
| System config | ❌ | ❌ | ✅ |
| View audit logs | ❌ | ❌ | ✅ |

## Security Features

- Password complexity requirements
- Account lockout after failed attempts
- Session timeout management
- JWT token rotation
- Role-based access control
- API rate limiting
- Audit logging
- Multi-tenant data isolation

## Testing

```bash
npm test
```

## Deployment

### Docker
```bash
docker-compose up -d
```

### Production Build
```bash
cd client && npm run build
npm start
```

## Documentation

- [API Documentation](./docs/API.md)
- [User Guide - Operator](./docs/USER_GUIDE_OPERATOR.md)
- [User Guide - Analyst](./docs/USER_GUIDE_ANALYST.md)
- [Admin Guide](./docs/ADMIN_GUIDE.md)
- [Architecture](./docs/ARCHITECTURE.md)

## License

MIT
