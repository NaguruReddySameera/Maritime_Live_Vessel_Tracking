# Maritime Vessel Tracking Platform - Django Backend

## Overview
Production-grade Django + Django REST Framework backend for maritime vessel tracking with role-based access control, real-time AIS data integration, and comprehensive analytics.

## Tech Stack
- **Framework:** Django 4.2.8 + Django REST Framework 3.14
- **Authentication:** JWT (djangorestframework-simplejwt) with Argon2 password hashing
- **Database:** PostgreSQL (production) / SQLite (development)
- **Task Queue:** Celery + Redis for background jobs
- **APIs:** MarineTraffic/AIS-Hub, UNCTAD, NOAA

## Features

### 1. Authentication & Authorization ✅
- **Login Flow:** Email validation → User lookup → Account status check → Password verification (Argon2) → JWT generation
- **Three-tier roles:** Operator, Analyst, Admin with granular permissions
- **Security:** Account lockout after failed attempts, session tracking, audit logging
- **Endpoints:**
  - `POST /api/auth/login/` - User login with JWT tokens
  - `POST /api/auth/register/` - User registration (admin only)
  - `POST /api/auth/logout/` - Logout and token blacklisting
  - `POST /api/auth/token/refresh/` - Refresh access token
  - `GET/PUT /api/auth/profile/` - User profile management
  - `POST /api/auth/change-password/` - Password change
  - `GET /api/auth/users/` - List users (admin only)
  - `GET/PUT/DELETE /api/auth/users/{id}/` - Manage users (admin only)

### 2. Vessel Tracking 🚢
- **Live tracking** with AIS data integration
- **Historical position data** for voyage replay
- **Vessel notes** for operational observations
- **Route planning** with waypoints
- **Models:** Vessel, VesselPosition, VesselNote, VesselRoute

### 3. Port Analytics (In Progress)
- Port congestion monitoring
- Port statistics from UNCTAD
- Historical trends

### 4. Safety Overlays (In Progress)
- Storm tracking (NOAA API)
- Piracy zones
- Incident reports
- Safety alerts

### 5. Voyage Replay (In Progress)
- Historical track playback
- Speed and course analysis

### 6. Dashboards (In Progress)
- Role-based dashboard widgets
- Custom visualizations
- Scheduled reports

### 7. Notifications (In Progress)
- Real-time alerts
- Email notifications

### 8. Admin Tools (In Progress)
- Audit logs
- System health monitoring
- User management
- Configuration

## Project Structure

```
backend/
├── maritime_project/        # Django project settings
│   ├── settings.py         # Configuration with JWT, CORS, security
│   ├── urls.py             # URL routing
│   ├── wsgi.py             # WSGI config
│   └── asgi.py             # ASGI config
├── apps/
│   ├── core/               # Shared utilities
│   │   ├── models.py       # Base models (TimeStampedModel, SoftDeleteModel)
│   │   ├── exceptions.py   # Custom exception handler
│   │   └── views.py        # Health check endpoints
│   ├── authentication/     # User management & JWT auth ✅
│   │   ├── models.py       # User, UserSession, AuditLog
│   │   ├── serializers.py  # DRF serializers
│   │   ├── views.py        # Login, registration, profile
│   │   ├── services.py     # Business logic
│   │   ├── permissions.py  # Role-based permissions
│   │   └── urls.py         # Auth routes
│   ├── vessels/            # Vessel tracking ⏳
│   │   ├── models.py       # Vessel, VesselPosition, VesselNote, VesselRoute
│   │   ├── serializers.py  # (To be created)
│   │   ├── views.py        # (To be created)
│   │   ├── services.py     # AIS integration
│   │   └── urls.py         # Vessel routes
│   ├── ports/              # Port management (Planned)
│   ├── safety/             # Safety overlays (Planned)
│   ├── voyages/            # Voyage replay (Planned)
│   ├── notifications/      # Alert system (Planned)
│   ├── dashboards/         # Dashboard builder (Planned)
│   └── admin_tools/        # Admin utilities (Planned)
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ (optional for production)
- Redis 6+ (for Celery)

### Step 1: Clone and Setup Environment

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:
```env
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional - defaults to SQLite)
# DATABASE_URL=postgresql://user:password@localhost:5432/maritime_db

# Redis
REDIS_URL=redis://localhost:6379/0

# External APIs
MARINETRAFFIC_API_KEY=your-api-key
UNCTAD_API_KEY=your-api-key
NOAA_API_KEY=your-api-key
```

### Step 3: Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Step 4: Load Seed Data (Optional)

```bash
python manage.py seed_data
```

This creates test users:
- **Admin:** sameerareddy583@gmail.com / admin
- **Analyst:** analyst@maritimetracking.com / Analyst@123
- **Operator:** operator@maritimetracking.com / Operator@123

### Step 5: Run Development Server

```bash
# Start Django server
python manage.py runserver

# In another terminal, start Celery worker (for background tasks)
celery -A maritime_project worker -l info

# In another terminal, start Celery beat (for scheduled tasks)
celery -A maritime_project beat -l info
```

The API will be available at: `http://localhost:8000`

## API Documentation

### Swagger UI
Visit `http://localhost:8000/swagger/` for interactive API documentation.

### ReDoc
Visit `http://localhost:8000/redoc/` for detailed API documentation.

### Health Check
- `GET /api/health/` - Basic health status
- `GET /api/health/ready/` - Readiness check with dependencies

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Login Process                       │
└─────────────────────────────────────────────────────────────┘

1. Client sends POST /api/auth/login/
   {
     "email": "user@example.com",
     "password": "UserPassword123"
   }

2. Validate email format
   └─> Invalid → 400 Bad Request

3. Lookup user by email
   └─> Not found → 401 Unauthorized

4. Check account status
   ├─> is_active = False → 403 Account Inactive
   └─> account_locked_until > now → 403 Account Locked

5. Verify password (Argon2)
   ├─> Invalid → Record failed attempt → 401 Unauthorized
   └─> Valid → Reset failed attempts counter

6. Generate JWT tokens
   ├─> Access token (1 day validity)
   └─> Refresh token (7 days validity)

7. Create user session record

8. Log successful login to audit trail

9. Return response
   {
     "success": true,
     "data": {
       "access_token": "eyJ0eXAiOiJKV1QiLCJhb...",
       "refresh_token": "eyJ0eXAiOiJKV1QiLCJhb...",
       "token_type": "Bearer",
       "expires_in": 86400,
       "user": {
         "id": 1,
         "email": "user@example.com",
         "full_name": "John Doe",
         "role": "analyst"
       }
     }
   }
```

## Role-Based Permissions

### Operator
- ✅ View vessels and positions
- ✅ Add notes to vessels
- ✅ View ports
- ✅ View own dashboard

### Analyst
- ✅ All Operator permissions
- ✅ View analytics and reports
- ✅ View historical voyage data
- ✅ Create custom dashboards
- ✅ Access safety overlays
- ✅ Voyage replay

### Admin
- ✅ All Analyst permissions
- ✅ Manage users (create, update, deactivate)
- ✅ View audit logs
- ✅ Manage system configuration
- ✅ View system health metrics
- ✅ Manage vessels and ports
- ✅ View all dashboards

## External API Integration

### MarineTraffic / AIS-Hub
**Purpose:** Real-time vessel positions and AIS data

**Endpoints Used:**
- Get vessel position by MMSI
- Search vessels in area
- Get vessel details

**Configuration:** `MARINETRAFFIC_API_KEY` in `.env`

### UNCTAD
**Purpose:** Port statistics and cargo data

**Endpoints Used:**
- Get port statistics
- Trade statistics by port
- Container throughput data

**Configuration:** `UNCTAD_API_KEY` in `.env`

### NOAA
**Purpose:** Weather data and storm tracking

**Endpoints Used:**
- Active storms
- Weather forecasts
- Marine warnings

**Configuration:** `NOAA_API_KEY` in `.env`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest apps/authentication/tests/test_views.py

# Run with verbose output
pytest -v
```

## Security Features

### Password Security
- **Argon2** hashing algorithm (most secure)
- Minimum 8 characters
- Password validation rules
- Password change tracking

### Account Protection
- Failed login attempt tracking
- Automatic account lockout (5 failed attempts)
- 30-minute lockout duration
- IP address logging

### Token Security
- JWT with short-lived access tokens (1 day)
- Refresh token rotation
- Token blacklisting on logout
- Session tracking

### Audit Logging
- All authentication events
- User management actions
- Data access and modifications
- IP address and user agent tracking

## Production Deployment

### Environment Variables
```env
DEBUG=False
DJANGO_SECRET_KEY=long-random-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DATABASE_URL=postgresql://user:password@db-host:5432/maritime_db
REDIS_URL=redis://redis-host:6379/0

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Static Files
```bash
python manage.py collectstatic --noinput
```

### Database Migrations
```bash
python manage.py migrate --noinput
```

### Run with Gunicorn
```bash
gunicorn maritime_project.wsgi:application --bind 0.0.0.0:8000
```

## Docker Deployment

```bash
# Build image
docker build -t maritime-backend .

# Run container
docker-compose up -d
```

## Monitoring

### Logs
- Application logs: `logs/maritime.log`
- Celery logs: Standard output
- Django logs: `logs/django.log`

### Health Checks
- `/api/health/` - Basic health
- `/api/health/ready/` - Database + Redis connectivity

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U username -d maritime_db -h localhost
```

### Redis Connection Issues
```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

### Migration Issues
```bash
# Reset migrations (development only)
python manage.py migrate authentication zero
python manage.py migrate --fake authentication zero
rm apps/authentication/migrations/00*.py

# Recreate migrations
python manage.py makemigrations
python manage.py migrate
```

## Contributing

### Code Style
- Follow PEP 8
- Use Black formatter
- Type hints where appropriate

### Commit Messages
- Use conventional commits format
- Examples:
  - `feat: add vessel route planning`
  - `fix: resolve login token expiration`
  - `docs: update API documentation`

## License
Proprietary - All rights reserved

## Support
For issues or questions, contact: dev@maritimetracking.com

## Roadmap

### Phase 1 (Current) ✅
- [x] Authentication system with JWT
- [x] User management
- [x] Audit logging
- [x] Vessel models

### Phase 2 (In Progress)
- [ ] Complete vessel tracking views and serializers
- [ ] AIS data integration service
- [ ] Port management
- [ ] Safety overlays

### Phase 3 (Planned)
- [ ] Voyage replay functionality
- [ ] Dashboard builder
- [ ] Notification system
- [ ] Admin tools

### Phase 4 (Future)
- [ ] WebSocket for real-time updates
- [ ] Mobile API optimization
- [ ] Advanced analytics
- [ ] Reporting engine
