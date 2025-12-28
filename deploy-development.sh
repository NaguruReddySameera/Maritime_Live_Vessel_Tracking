#!/bin/bash

# Maritime Tracking System - Development Deployment Script
# Deploys with SQLite database

set -e

echo "═══════════════════════════════════════════════════════════"
echo "Maritime Tracking System - Development Deployment"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if .env.development exists
if [ ! -f .env.development ]; then
    echo "❌ Error: .env.development file not found!"
    echo "Please create .env.development with your development settings."
    exit 1
fi

# Copy development env file
cp .env.development backend/.env
echo "✅ Loaded development environment variables"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.dev.yml down

# Build images
echo "🏗️  Building Docker images..."
docker-compose -f docker-compose.dev.yml build

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for backend
echo "⏳ Waiting for backend..."
sleep 5

# Run migrations
echo "📦 Running database migrations..."
docker-compose -f docker-compose.dev.yml exec backend-dev python manage.py migrate

# Create superuser
echo "👤 Creating admin user..."
docker-compose -f docker-compose.dev.yml exec backend-dev python manage.py shell -c "
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

# Seed initial data
echo "🌱 Seeding initial data..."
docker-compose -f docker-compose.dev.yml exec backend-dev python manage.py seed_data || echo "⚠️  Seed data command not found, skipping..."

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ DEVELOPMENT DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🔗 Services:"
echo "   • Frontend:  http://localhost:3000"
echo "   • Backend:   http://localhost:8000"
echo "   • Admin:     http://localhost:8000/admin/"
echo ""
echo "📊 Database:"
echo "   • SQLite: ./backend/db.sqlite3"
echo ""
echo "📝 View logs:"
echo "   docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose -f docker-compose.dev.yml down"
echo ""
echo "═══════════════════════════════════════════════════════════"
