# Maritime Tracking System - Deployment Guide

## Overview

This deployment setup supports both **Development** (SQLite) and **Production** (PostgreSQL) environments using Docker and Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git
- 4GB RAM minimum (8GB recommended for production)

## Quick Start

### Development Deployment (SQLite)

```bash
# 1. Clone repository
git clone <repository-url>
cd Live_tracking

# 2. Create development environment file
cp .env.development backend/.env

# 3. Deploy development environment
./deploy-development.sh

# 4. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### Production Deployment (PostgreSQL)

```bash
# 1. Create production environment file
cp .env.production .env

# 2. Update .env with your production settings
# IMPORTANT: Change SECRET_KEY, DB_PASSWORD, and other sensitive values

# 3. Deploy production environment
./deploy-production.sh

# 4. Access the application
# Application: http://localhost (via Nginx)
# Backend API: http://localhost/api/
```

## Environment Configuration

### Development (.env.development)
- **Database**: SQLite (file-based, no separate DB server)
- **Debug**: Enabled
- **Hot Reload**: Enabled for both frontend and backend
- **CORS**: Permissive (allows localhost origins)

### Production (.env.production)
- **Database**: PostgreSQL (separate container)
- **Debug**: Disabled
- **Reverse Proxy**: Nginx
- **Caching**: Redis
- **Security**: Strict CORS, HTTPS ready

## Architecture

### Development Stack
```
┌─────────────────────────────────────┐
│   Frontend (React Dev Server)      │
│   Port: 3000                        │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Backend (Django Dev Server)      │
│   Port: 8000                        │
│   Database: SQLite (file)           │
└─────────────────────────────────────┘
```

### Production Stack
```
┌──────────────────────────────────────┐
│         Nginx (Port 80/443)          │
│      Reverse Proxy + SSL/TLS         │
└─────┬───────────────────────┬────────┘
      │                       │
      ▼                       ▼
┌──────────────┐      ┌───────────────────┐
│   Frontend   │      │    Backend API    │
│  (React App) │      │  (Django + DRF)   │
│   Port: 80   │      │    Port: 8000     │
└──────────────┘      └─────────┬─────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
              ┌─────────────┐      ┌──────────────┐
              │ PostgreSQL  │      │    Redis     │
              │  Port: 5432 │      │  Port: 6379  │
              └─────────────┘      └──────────────┘
```

## Database Management

### SQLite (Development)

```bash
# Access database
docker-compose -f docker-compose.dev.yml exec backend-dev python manage.py dbshell

# Backup database
cp backend/db.sqlite3 backend/db.sqlite3.backup

# Reset database
docker-compose -f docker-compose.dev.yml exec backend-dev python manage.py flush
```

### PostgreSQL (Production)

```bash
# Access database
docker-compose exec db psql -U maritime_user -d maritime_tracking

# Backup database
docker-compose exec db pg_dump -U maritime_user maritime_tracking > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U maritime_user -d maritime_tracking

# View database size
docker-compose exec db psql -U maritime_user -d maritime_tracking -c "
SELECT pg_size_pretty(pg_database_size('maritime_tracking'));"
```

## Common Commands

### View Logs
```bash
# Development
docker-compose -f docker-compose.dev.yml logs -f

# Production
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Restart Services
```bash
# Development
docker-compose -f docker-compose.dev.yml restart

# Production
docker-compose restart
```

### Stop Services
```bash
# Development
docker-compose -f docker-compose.dev.yml down

# Production
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Scale Services (Production)
```bash
# Scale backend workers
docker-compose up -d --scale backend=3
```

## Database Migrations

```bash
# Create migrations
docker-compose exec backend python manage.py makemigrations

# Apply migrations
docker-compose exec backend python manage.py migrate

# View migration status
docker-compose exec backend python manage.py showmigrations
```

## Admin User

### Default Credentials
- **Email**: sameerareddy583@gmail.com
- **Password**: Admin@123456

### Create Additional Admin
```bash
docker-compose exec backend python manage.py createsuperuser
```

## Monitoring

### Health Checks
```bash
# Backend health
curl http://localhost:8000/api/auth/demo-users/

# Frontend health
curl http://localhost:3000/

# Nginx health (production)
curl http://localhost/health
```

### Resource Usage
```bash
# View container stats
docker stats

# View disk usage
docker system df
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:5432 | xargs kill -9  # PostgreSQL
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Frontend Build Issues
```bash
# Clear node_modules and rebuild
docker-compose -f docker-compose.dev.yml exec frontend-dev rm -rf node_modules
docker-compose -f docker-compose.dev.yml exec frontend-dev npm install
```

### Backend Issues
```bash
# Clear Python cache
docker-compose exec backend find . -type d -name __pycache__ -exec rm -r {} +

# Rebuild backend image
docker-compose build --no-cache backend
```

## Security Considerations

### Production Checklist

- [ ] Change `SECRET_KEY` in .env.production
- [ ] Update `DB_PASSWORD` to a strong password
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable HTTPS redirect in Nginx
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Enable rate limiting
- [ ] Set up monitoring (e.g., Sentry, DataDog)

### SSL/TLS Setup (Production)

1. Obtain SSL certificates (Let's Encrypt recommended):
```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d yourdomain.com
```

2. Update Nginx configuration in `docker/nginx/conf.d/default.conf`

## Performance Optimization

### Database Optimization (PostgreSQL)

```sql
-- Create indexes for better performance
CREATE INDEX idx_vessels_location ON vessels_vessel USING GIST(current_coordinates);
CREATE INDEX idx_notifications_user_read ON notifications_notification(user_id, is_read);
```

### Caching (Production)

Redis is included in production setup for caching:
```python
# In settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
    }
}
```

## Backup Strategy

### Automated Backups

Create a cron job for automated backups:

```bash
# Add to crontab (crontab -e)
0 2 * * * /path/to/backup-script.sh
```

backup-script.sh:
```bash
#!/bin/bash
BACKUP_DIR="/backups/maritime"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T db pg_dump -U maritime_user maritime_tracking > \
    ${BACKUP_DIR}/db_${TIMESTAMP}.sql

# Backup media files
docker cp maritime_backend:/app/media ${BACKUP_DIR}/media_${TIMESTAMP}

# Keep only last 7 days
find ${BACKUP_DIR} -name "db_*.sql" -mtime +7 -delete
find ${BACKUP_DIR} -name "media_*" -mtime +7 -exec rm -rf {} +
```

## Updating the Application

```bash
# Pull latest changes
git pull origin main

# Development
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml exec backend-dev python manage.py migrate

# Production
docker-compose down
docker-compose build
docker-compose up -d
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput
```

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review this guide
- Check Docker documentation
- Review Django documentation

## License

[Your License Here]
