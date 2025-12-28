# Getting Started with Maritime Vessel Tracking Platform

## Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 14+ (optional, SQLite works for development)
- Redis 6+ (for Celery background tasks)
- Git

### Step-by-Step Installation

#### 1. Clone and Navigate

```bash
cd /home/mastan/Music/Live_tracking/backend
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Expected output: Installation of ~30 packages including Django, DRF, JWT, etc.

#### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your preferred editor
nano .env  # or vim, or code .env
```

**Minimal configuration for development:**
```env
DEBUG=True
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Leave these empty for SQLite (development)
# DATABASE_URL=

# Redis (install locally or use Docker)
REDIS_URL=redis://localhost:6379/0

# External APIs (optional - can be empty for now)
MARINETRAFFIC_API_KEY=
UNCTAD_API_KEY=
NOAA_API_KEY=
```

#### 5. Database Setup

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: admin, auth, authentication, contenttypes, sessions, vessels
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying authentication.0001_initial... OK
#   ...
```

#### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser

# You'll be prompted for:
# Email: admin@example.com
# First name: Admin
# Last name: User
# Password: (your secure password)
```

#### 7. Load Seed Data (Recommended)

```bash
python manage.py seed_data
```

This creates 3 test users:
- **Admin:** sameerareddy583@gmail.com / admin
- **Analyst:** analyst@maritimetracking.com / Analyst@123
- **Operator:** operator@maritimetracking.com / Operator@123

Plus 3 sample vessels with position history.

#### 8. Start Development Server

```bash
python manage.py runserver
```

Expected output:
```
Performing system checks...
System check identified no issues (0 silenced).
January 10, 2025 - 10:00:00
Django version 4.2.8, using settings 'maritime_project.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

#### 9. Verify Installation

Open browser and visit:
- **API Root:** http://localhost:8000/api/
- **Swagger Docs:** http://localhost:8000/swagger/
- **Health Check:** http://localhost:8000/api/health/

Expected response from health check:
```json
{
  "status": "healthy",
  "service": "Maritime Vessel Tracking API",
  "version": "1.0.0"
}
```

### Testing the API

#### Login Request

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@maritimetracking.com",
    "password": "admin"
  }'
```

Expected response:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhb...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhb...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "email": "sameerareddy583@gmail.com",
      "full_name": "Admin User",
      "role": "admin"
    }
  }
}
```

#### Get User Profile

```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Optional: Start Celery (Background Tasks)

In a **separate terminal**, with virtual environment activated:

```bash
# Start Celery worker
celery -A maritime_project worker -l info

# In another terminal, start Celery beat (scheduler)
celery -A maritime_project beat -l info
```

### Docker Setup (Alternative)

If you prefer Docker:

```bash
# From backend directory
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Load seed data
docker-compose exec backend python manage.py seed_data

# View logs
docker-compose logs -f backend
```

Access at: http://localhost:8000

### Troubleshooting

#### "No module named 'maritime_project'"
- Make sure you're in the `backend/` directory
- Virtual environment is activated
- Dependencies are installed

#### "Database locked" (SQLite)
- Close any database browser tools
- Only one process can write to SQLite at a time
- Consider using PostgreSQL for multi-user scenarios

#### "Connection refused" (Redis)
- Install Redis: `sudo apt install redis-server` (Ubuntu/Debian)
- Or via Docker: `docker run -d -p 6379:6379 redis:alpine`
- Verify: `redis-cli ping` should return `PONG`

#### "Migrations not applied"
```bash
python manage.py showmigrations  # Check migration status
python manage.py migrate  # Apply pending migrations
```

#### "CORS errors" (when testing with frontend)
- Add frontend URL to `CORS_ALLOWED_ORIGINS` in `settings.py`
- Or set `CORS_ALLOW_ALL_ORIGINS = True` (development only)

### Project Structure Overview

```
backend/
├── maritime_project/           # Django project
│   ├── settings.py            # Configuration
│   ├── urls.py                # Main URL routing
│   ├── celery.py              # Celery config
│   └── wsgi.py/asgi.py        # Server configs
│
├── apps/                      # Django applications
│   ├── core/                  # Shared utilities
│   │   ├── models.py          # Base models
│   │   ├── exceptions.py      # Error handling
│   │   └── views.py           # Health checks
│   │
│   ├── authentication/        # Auth system ✅
│   │   ├── models.py          # User, Session, AuditLog
│   │   ├── views.py           # Login, register, profile
│   │   ├── serializers.py     # Data validation
│   │   ├── permissions.py     # RBAC
│   │   └── urls.py            # Auth endpoints
│   │
│   └── vessels/               # Vessel tracking ⏳
│       └── models.py          # Vessel, Position, Note, Route
│
├── manage.py                  # Django CLI
├── requirements.txt           # Python dependencies
├── .env                       # Environment config
└── README.md                  # Documentation
```

### Next Steps

1. **Explore API Documentation**
   - Visit http://localhost:8000/swagger/
   - Try the interactive API tester

2. **Test Authentication**
   - Login with test credentials
   - Try creating/updating user profile
   - Test password change

3. **Review Code**
   - Check `apps/authentication/models.py` for User model
   - Look at `apps/authentication/views.py` for login flow
   - Understand role-based permissions in `permissions.py`

4. **Start Development**
   - Continue with vessel tracking endpoints
   - Add port management module
   - Implement safety overlays

### Useful Commands

```bash
# Create new Django app
python manage.py startapp appname

# Make migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell (interactive Python)
python manage.py shell

# Run tests
pytest

# Check for issues
python manage.py check

# Collect static files (production)
python manage.py collectstatic

# View all available commands
python manage.py help
```

### Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/vessel-endpoints
   ```

2. **Make changes**
   - Edit models, views, serializers
   - Update URLs

3. **Create/apply migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Test changes**
   ```bash
   python manage.py runserver
   # Test in browser or with curl
   ```

5. **Write tests**
   ```python
   # apps/vessels/tests/test_views.py
   def test_vessel_list():
       # Test code
   ```

6. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add vessel list endpoint"
   git push origin feature/vessel-endpoints
   ```

### Additional Resources

- **Django Documentation:** https://docs.djangoproject.com/
- **DRF Documentation:** https://www.django-rest-framework.org/
- **JWT Documentation:** https://django-rest-framework-simplejwt.readthedocs.io/
- **Celery Documentation:** https://docs.celeryproject.org/

### Support

For questions or issues:
- Check the main README.md
- Review API documentation at /swagger/
- Check logs in `logs/maritime.log`

---

**You're all set!** 🚀

The backend is now running with:
- ✅ JWT authentication
- ✅ Role-based access control
- ✅ User management
- ✅ Audit logging
- ✅ Health checks
- ✅ API documentation

Next: Complete vessel tracking module and add external API integrations.
