# Hospital Management System (HMS)

A comprehensive Django-based hospital management system for efficient healthcare administration.

## 🏥 Features

### Core Functionality
- **User Management**: Role-based authentication (Admin, Doctor, Patient)
- **Appointment System**: Booking, scheduling, confirmation, and management
- **Medical Records**: Comprehensive patient medical history
- **Dashboard**: Real-time analytics and role-based interfaces
- **Notifications**: Email notifications and reminders
- **Advanced Search**: Multi-field search with filtering
- **Data Export**: CSV and Excel export capabilities
- **Analytics**: Visual charts and performance metrics

### Technical Features
- **Django 4.2.7** with modern Python practices
- **Bootstrap 5** responsive design
- **PostgreSQL/MySQL** database support
- **Redis** caching for performance
- **Docker** containerization
- **Security headers** and middleware
- **Automated backups** and deployment scripts

## 🚀 Quick Start

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd HMS
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - URL: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Default credentials: admin / admin123

## 🏭 Production Deployment

### Option 1: Docker Deployment (Recommended)

1. **Configure environment variables**
   ```bash
   cp .env.example .env.production
   # Edit .env.production with production values
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker/docker-compose.prod.yml up -d --build
   ```

### Option 2: Manual Deployment

1. **Install production dependencies**
   ```bash
   pip install -r requirements/production.txt
   ```

2. **Run deployment script**
   ```bash
   ./scripts/deploy.sh
   ```

### Option 3: Using Management Commands

1. **Create backup**
   ```bash
   python manage.py backup
   ```

2. **Deploy application**
   ```bash
   python manage.py deploy
   ```

## 📊 System Architecture

```
┌─────────────────┐
│   Nginx       │  ← Load Balancer & Static File Serving
│   (Port 80/443)│
└─────────────────┘
        │
        ▼
┌─────────────────┐
│   Gunicorn      │  ← WSGI Application Server
│   (Port 8000)   │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│   Django App    │  ← Web Application
│                 │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│   PostgreSQL    │  ← Database
│   Redis         │  ← Cache
└─────────────────┘
```

## 🔐 Security Features

- **Role-based Access Control**: Admin, Doctor, Patient roles
- **Object-level Permissions**: Users can only access their own data
- **Security Headers**: XSS protection, content type sniffing prevention
- **CSRF Protection**: Cross-site request forgery prevention
- **Secure Sessions**: HTTP-only, secure cookies
- **SQL Injection Protection**: Django ORM parameterized queries

## 📈 Monitoring & Logging

- **Application Logging**: Structured logging with rotation
- **Performance Monitoring**: Request time tracking
- **Health Checks**: Django health check endpoints
- **Error Tracking**: Sentry integration for error monitoring
- **Backup Automation**: Scheduled database and media backups

## 🎯 User Roles & Permissions

### Admin
- Full system access
- User management
- All appointment viewing
- Analytics and reporting
- System configuration

### Doctor
- Manage own appointments
- Create medical records
- View patient history
- Manage schedule and holidays

### Patient
- Book appointments
- View own appointments
- Submit feedback
- Access medical records

## 📱 Responsive Design

- **Mobile-first approach**: Optimized for all screen sizes
- **Bootstrap 5**: Modern UI framework
- **Progressive Enhancement**: Works without JavaScript
- **Accessibility**: WCAG 2.1 AA compliance

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=hms_prod
DB_USER=hms_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Security
SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Cache
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
REDIS_URL=redis://localhost:6379/0

# Monitoring
SENTRY_DSN=your_sentry_dsn
```

## 📁 Project Structure

```
HMS/
├── hms_core/           # Django project settings
│   ├── settings.py     # Development settings
│   ├── production_settings.py  # Production settings
│   ├── wsgi.py        # WSGI configuration
│   └── middleware.py   # Custom middleware
├── accounts/           # User management app
├── appointments/       # Appointment system app
├── dashboard/          # Dashboard app
├── templates/          # HTML templates
├── static/            # CSS, JS, images
├── media/             # User uploads
├── docker/            # Docker configuration
├── scripts/           # Deployment scripts
├── requirements/       # Python dependencies
└── logs/              # Application logs
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📞 Support

### Common Issues

1. **Migration Errors**: Ensure database is running and accessible
2. **Static Files**: Run `collectstatic` after template changes
3. **Permission Denied**: Check user roles and permissions
4. **Email Issues**: Verify SMTP settings and credentials

### Getting Help

- **Documentation**: Check inline code documentation
- **Logs**: Review `logs/hms.log` for errors
- **Health Check**: Access `/health/` endpoint
- **Performance**: Monitor response times and database queries

## 🔄 Maintenance

### Regular Tasks

1. **Daily**: Automated backups, log rotation
2. **Weekly**: Security updates, performance review
3. **Monthly**: Database optimization, cleanup old backups
4. **Quarterly**: Security audit, dependency updates

### Backup Strategy

- **Database**: Daily automated backups with 30-day retention
- **Media**: Weekly backups with versioning
- **Configuration**: Version-controlled settings backup
- **Recovery**: Tested restoration procedures

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📊 Performance Metrics

Target performance benchmarks:
- **Page Load Time**: < 2 seconds
- **Database Query Time**: < 500ms
- **API Response Time**: < 200ms
- **Uptime**: > 99.9%
- **Mobile Performance**: > 90 score

## 🔮 Future Enhancements

- **Mobile App**: React Native mobile application
- **API Integration**: RESTful API for third-party integrations
- **AI Features**: Smart scheduling and recommendations
- **Telemedicine**: Video consultation capabilities
- **Multi-tenant**: Support for multiple hospitals

---

**Built with ❤️ using Django, Bootstrap, and modern web technologies.**
