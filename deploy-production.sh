#!/bin/bash

# Maritime Tracking System - Production Deployment Script
# Deploys with PostgreSQL database

set -e

echo "═══════════════════════════════════════════════════════════"
echo "Maritime Tracking System - Production Deployment"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please create .env.production with your production settings."
    exit 1
fi

# Copy production env file
cp .env.production .env
echo "✅ Loaded production environment variables"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build images
echo "🏗️  Building Docker images..."
docker-compose build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for database
echo "⏳ Waiting for database..."
sleep 10

# Run migrations
echo "📦 Running database migrations..."
docker-compose exec backend python manage.py migrate

# Create superuser (if needed)
echo "👤 Creating admin user..."
docker-compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(email='sameerareddy583@gmail.com').exists():
    User.objects.create_superuser(
        email='sameerareddy583@gmail.com',
        password='Admin@123456',
        first_name='Admin',
        last_name='User',
        role='admin'
    );
    print('Admin user created');
else:
    print('Admin user already exists');
"

# Collect static files
echo "📂 Collecting static files..."
docker-compose exec backend python manage.py collectstatic --noinput

# Seed initial data
echo "🌱 Seeding initial data..."
docker-compose exec backend python manage.py seed_data || echo "⚠️  Seed data already exists or command not found"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🔗 Services:"
echo "   • Frontend:  http://localhost"
echo "   • Backend:   http://localhost/api/"
echo "   • Admin:     http://localhost:8000/admin/"
echo ""
echo "📊 Database:"
echo "   • PostgreSQL: localhost:5432"
echo "   • Database: maritime_tracking"
echo ""
echo "📝 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
echo "═══════════════════════════════════════════════════════════"
