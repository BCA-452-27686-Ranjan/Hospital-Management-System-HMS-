#!/bin/bash

# HMS Production Deployment Script
# This script automates the deployment process for HMS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in production environment
if [ "$DJANGO_SETTINGS_MODULE" != "hms_core.production_settings" ]; then
    print_warning "Not running in production mode. Setting production environment..."
    export DJANGO_SETTINGS_MODULE=hms_core.production_settings
fi

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    print_error "Virtual environment is not activated. Please activate your virtual environment first."
    exit 1
fi

print_status "Starting HMS deployment process..."

# Step 1: Update dependencies
print_status "Updating Python dependencies..."
pip install -r requirements/production.txt

# Step 2: Run pre-deployment checks
print_status "Running pre-deployment checks..."
python manage.py check --deploy

# Step 3: Create backup
print_status "Creating backup..."
python manage.py backup

# Step 4: Run database migrations
print_status "Running database migrations..."
python manage.py migrate --noinput

# Step 5: Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Step 6: Create necessary directories
print_status "Creating production directories..."
mkdir -p logs staticfiles media backups

# Step 7: Set proper permissions
print_status "Setting file permissions..."
chmod -R 755 staticfiles media logs
find staticfiles -type f -exec chmod 644 {} \;
find media -type f -exec chmod 644 {} \;
find logs -type f -exec chmod 644 {} \;

# Step 8: Restart application services
if command -v docker-compose &> /dev/null; then
    print_status "Restarting Docker services..."
    docker-compose -f docker/docker-compose.prod.yml down
    docker-compose -f docker/docker-compose.prod.yml up -d --build
elif command -v systemctl &> /dev/null; then
    print_status "Restarting application services..."
    sudo systemctl reload nginx
    sudo systemctl restart gunicorn
    sudo systemctl enable gunicorn
else
    print_warning "Neither docker-compose nor systemctl found. Please restart your web server manually."
fi

# Step 9: Health check
print_status "Running health check..."
sleep 5  # Wait for services to start

if command -v curl &> /dev/null; then
    if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
        print_status "✅ Application is running and healthy!"
    else
        print_error "❌ Application health check failed!"
        exit 1
    fi
else
    print_warning "curl not found. Please check application manually."
fi

# Step 10: Clean up old backups
print_status "Cleaning up old backups (keeping last 30 days)..."
find backups -name "*.sql" -mtime +30 -delete
find backups -name "*.sqlite3" -mtime +30 -delete
find backups -name "*.zip" -mtime +30 -delete 2>/dev/null || true

print_status "🚀 HMS deployment completed successfully!"
print_status "Application is now running in production mode."

# Display next steps
echo ""
print_status "Next steps:"
echo "1. Monitor application logs: tail -f logs/hms.log"
echo "2. Check performance: Access your monitoring dashboard"
echo "3. Update DNS: Point your domain to the server IP"
echo "4. Configure SSL: Set up SSL certificate for HTTPS"
echo "5. Monitor backups: Check backup directory regularly"
echo ""
print_status "For issues, check the logs at: logs/hms.log"
