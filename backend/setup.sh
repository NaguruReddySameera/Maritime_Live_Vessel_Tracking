#!/bin/bash

# Maritime Vessel Tracking - Quick Setup Script
# This script automates the initial setup process

set -e  # Exit on error

echo "🚢 Maritime Vessel Tracking Platform - Setup Script"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Please run this script from the backend directory"
    exit 1
fi

# Step 1: Create virtual environment
echo "📦 Step 1: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Step 2: Activate virtual environment and install dependencies
echo "📦 Step 2: Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Step 3: Setup environment file
echo "⚙️  Step 3: Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✓ .env file already exists"
fi
echo ""

# Step 4: Create logs directory
echo "📝 Step 4: Creating logs directory..."
mkdir -p logs
echo "✓ Logs directory created"
echo ""

# Step 5: Database setup
echo "🗄️  Step 5: Setting up database..."
python manage.py makemigrations
python manage.py migrate
echo "✓ Database migrations completed"
echo ""

# Step 6: Load seed data
echo "🌱 Step 6: Loading seed data..."
read -p "Do you want to load test data? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py seed_data
    echo "✓ Seed data loaded"
    echo ""
    echo "📧 Test User Credentials:"
    echo "  Admin:    admin@maritimetracking.com / Admin@123456"
    echo "  Analyst:  analyst@maritimetracking.com / Analyst@123"
    echo "  Operator: operator@maritimetracking.com / Operator@123"
else
    echo "⏭️  Skipped seed data"
fi
echo ""

# Step 7: Run system checks
echo "🔍 Step 7: Running system checks..."
python manage.py check
echo "✓ System checks passed"
echo ""

echo "=================================================="
echo "🎉 Setup completed successfully!"
echo ""
echo "📚 Next steps:"
echo "  1. Review and edit .env file if needed"
echo "  2. Start the development server:"
echo "     source venv/bin/activate"
echo "     python manage.py runserver"
echo ""
echo "  3. Access the API:"
echo "     http://localhost:8000/api/"
echo "     http://localhost:8000/swagger/"
echo ""
echo "  4. (Optional) Start Celery worker:"
echo "     celery -A maritime_project worker -l info"
echo ""
echo "📖 For detailed instructions, see GETTING_STARTED.md"
echo "=================================================="
