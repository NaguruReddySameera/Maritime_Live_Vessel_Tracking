# Quick Start - Django Backend

## Installation

### Option 1: Automated Setup (Recommended)
```bash
cd /home/mastan/Music/Live_tracking/backend
./setup.sh
```

### Option 2: Manual Setup

```bash
cd /home/mastan/Music/Live_tracking/backend

# Install python3-venv if needed (Ubuntu/Debian)
sudo apt install python3.10-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Load test data (optional)
python manage.py seed_data

# Start server
python manage.py runserver
```

## Access Points

- **API**: http://localhost:8000/api/
- **Swagger**: http://localhost:8000/swagger/
- **Admin**: http://localhost:8000/admin/
- **Health**: http://localhost:8000/api/health/

## Test Credentials

After running `python manage.py seed_data`:

| Role | Email | Password |
|------|-------|----------|
| Admin | sameerareddy583@gmail.com | admin |
| Analyst | analyst@maritimetracking.com | Analyst@123 |
| Operator | operator@maritimetracking.com | Operator@123 |

## Quick API Test

### 1. Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"sameerareddy583@gmail.com","password":"admin"}'
```

Copy the `access_token` from response.

### 2. List Vessels
```bash
curl http://localhost:8000/api/vessels/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Get Vessel Details
```bash
curl http://localhost:8000/api/vessels/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run server
python manage.py runserver

# Make migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load test data
python manage.py seed_data

# Django shell
python manage.py shell

# Celery worker
celery -A maritime_project worker -l info

# Celery beat
celery -A maritime_project beat -l info
```

## Docker

```bash
cd backend

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Load seed data
docker-compose exec backend python manage.py seed_data

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Project Structure

```
backend/
├── maritime_project/       # Django config
│   ├── settings.py        # Main settings
│   ├── urls.py            # URL routing
│   └── celery.py          # Celery config
├── apps/
│   ├── authentication/    # ✅ Auth & users
│   ├── vessels/          # ✅ Vessel tracking
│   └── core/             # ✅ Shared utilities
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Available Modules

| Module | Status | Endpoints |
|--------|--------|-----------|
| Authentication | ✅ Complete | 11 endpoints |
| Vessels | ✅ Complete | 24 endpoints |
| Ports | 📋 Planned | - |
| Safety | 📋 Planned | - |
| Dashboards | 📋 Planned | - |

## Documentation

- **`README.md`** - Complete documentation
- **`GETTING_STARTED.md`** - Detailed setup guide
- **`VESSEL_API.md`** - Vessel API reference
- **`IMPLEMENTATION_STATUS.md`** - Project status
- **Swagger UI** - Interactive docs at /swagger/

## Troubleshooting

### Virtual Environment Error
```bash
# Install python3-venv
sudo apt install python3.10-venv
```

### Database Locked
```bash
# Close other connections to SQLite
# Or use PostgreSQL for production
```

### Redis Connection Error
```bash
# Install Redis
sudo apt install redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

### Port Already in Use
```bash
# Use different port
python manage.py runserver 8001
```

## Getting Help

1. Check logs: `logs/maritime.log`
2. Review documentation in `docs/` folder
3. Visit Swagger UI for API reference
4. Run `python manage.py check` for issues

## Next Steps

1. ✅ Test authentication endpoints
2. ✅ Test vessel tracking API
3. 📋 Build port management module
4. 📋 Add safety overlays
5. 📋 Create React frontend

---

**Current Status**: Authentication ✅ | Vessels ✅ | Ready for Testing 🚀
