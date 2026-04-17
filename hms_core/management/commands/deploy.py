from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Deploy HMS application with production optimizations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-backup',
            action='store_true',
            help='Skip backup before deployment',
        )
        parser.add_argument(
            '--skip-migrate',
            action='store_true',
            help='Skip database migrations',
        )
        parser.add_argument(
            '--skip-collectstatic',
            action='store_true',
            help='Skip static file collection',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting HMS deployment...'))
        
        # Step 1: Create backup (unless skipped)
        if not options['skip_backup']:
            self.stdout.write('Creating backup...')
            call_command('backup')
            self.stdout.write(self.style.SUCCESS('✓ Backup completed'))
        
        # Step 2: Run migrations (unless skipped)
        if not options['skip_migrate']:
            self.stdout.write('Running database migrations...')
            call_command('migrate')
            self.stdout.write(self.style.SUCCESS('✓ Migrations completed'))
        
        # Step 3: Collect static files (unless skipped)
        if not options['skip_collectstatic']:
            self.stdout.write('Collecting static files...')
            call_command('collectstatic', '--noinput', '--clear')
            self.stdout.write(self.style.SUCCESS('✓ Static files collected'))
        
        # Step 4: Create production directories
        self.create_production_directories()
        
        # Step 5: Set proper permissions
        self.set_permissions()
        
        # Step 6: Health check
        self.health_check()
        
        self.stdout.write(
            self.style.SUCCESS('🚀 HMS deployment completed successfully!')
        )

    def create_production_directories(self):
        """Create necessary directories for production"""
        directories = [
            getattr(settings, 'MEDIA_ROOT', 'media'),
            getattr(settings, 'STATIC_ROOT', 'staticfiles'),
            getattr(settings, 'BACKUP_STORAGE_PATH', 'backups'),
            os.path.join(settings.BASE_DIR, 'logs'),
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            self.stdout.write(f'✓ Directory created/verified: {directory}')

    def set_permissions(self):
        """Set proper permissions for production"""
        directories = [
            getattr(settings, 'MEDIA_ROOT', 'media'),
            getattr(settings, 'STATIC_ROOT', 'staticfiles'),
            getattr(settings, 'BACKUP_STORAGE_PATH', 'backups'),
            os.path.join(settings.BASE_DIR, 'logs'),
        ]
        
        for directory in directories:
            if os.path.exists(directory):
                # Set directory permissions to 755
                os.chmod(directory, 0o755)
                
                # Set file permissions recursively
                for root, dirs, files in os.walk(directory):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o755)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o644)
                
                self.stdout.write(f'✓ Permissions set for: {directory}')

    def health_check(self):
        """Run health checks"""
        self.stdout.write('Running health checks...')
        
        try:
            call_command('check', '--deploy')
            self.stdout.write(self.style.SUCCESS('✓ Health checks passed'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Health check failed: {e}')
            )
