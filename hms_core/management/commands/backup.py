from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import os
import shutil
import subprocess
from datetime import datetime

class Command(BaseCommand):
    help = 'Create backup of the HMS database and media files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--media-only',
            action='store_true',
            help='Backup only media files',
        )
        parser.add_argument(
            '--db-only',
            action='store_true',
            help='Backup only database',
        )

    def handle(self, *args, **options):
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = getattr(settings, 'BACKUP_STORAGE_PATH', 'backups')
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        if not options['media_only']:
            self.backup_database(backup_dir, timestamp)
        
        if not options['db_only']:
            self.backup_media(backup_dir, timestamp)
        
        self.stdout.write(
            self.style.SUCCESS(f'Backup completed successfully at {backup_dir}')
        )
        
        # Clean old backups
        self.clean_old_backups(backup_dir)

    def backup_database(self, backup_dir, timestamp):
        """Backup the database"""
        db_engine = settings.DATABASES['default']['ENGINE']
        
        if 'postgresql' in db_engine:
            self.backup_postgresql(backup_dir, timestamp)
        elif 'mysql' in db_engine:
            self.backup_mysql(backup_dir, timestamp)
        elif 'sqlite' in db_engine:
            self.backup_sqlite(backup_dir, timestamp)
        else:
            self.stdout.write(
                self.style.ERROR(f'Unsupported database engine: {db_engine}')
            )

    def backup_postgresql(self, backup_dir, timestamp):
        """Backup PostgreSQL database"""
        db_config = settings.DATABASES['default']
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sql')
        
        cmd = [
            'pg_dump',
            '-h', db_config['HOST'],
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '-f', backup_file,
            '--no-password',
        ]
        
        try:
            subprocess.run(cmd, check=True)
            self.stdout.write(
                self.style.SUCCESS(f'PostgreSQL backup created: {backup_file}')
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'PostgreSQL backup failed: {e}')
            )

    def backup_mysql(self, backup_dir, timestamp):
        """Backup MySQL database"""
        db_config = settings.DATABASES['default']
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sql')
        
        cmd = [
            'mysqldump',
            f'--host={db_config["HOST"]}',
            f'--user={db_config["USER"]}',
            f'--password={db_config["PASSWORD"]}',
            f'--databases={db_config["NAME"]}',
            '--result-file=' + backup_file,
            '--single-transaction',
            '--routines',
            '--triggers',
        ]
        
        try:
            subprocess.run(cmd, check=True)
            self.stdout.write(
                self.style.SUCCESS(f'MySQL backup created: {backup_file}')
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'MySQL backup failed: {e}')
            )

    def backup_sqlite(self, backup_dir, timestamp):
        """Backup SQLite database"""
        db_config = settings.DATABASES['default']
        db_path = db_config['NAME']
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sqlite3')
        
        try:
            shutil.copy2(db_path, backup_file)
            self.stdout.write(
                self.style.SUCCESS(f'SQLite backup created: {backup_file}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'SQLite backup failed: {e}')
            )

    def backup_media(self, backup_dir, timestamp):
        """Backup media files"""
        media_dir = getattr(settings, 'MEDIA_ROOT', 'media')
        if os.path.exists(media_dir):
            media_backup = os.path.join(backup_dir, f'media_backup_{timestamp}')
            shutil.make_archive(media_backup, 'zip', media_dir)
            self.stdout.write(
                self.style.SUCCESS(f'Media backup created: {media_backup}.zip')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Media directory not found')
            )

    def clean_old_backups(self, backup_dir):
        """Remove old backups based on retention policy"""
        retention_days = getattr(settings, 'BACKUP_RETENTION_DAYS', 30)
        cutoff_time = timezone.now() - timezone.timedelta(days=retention_days)
        
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        self.stdout.write(
                            self.style.SUCCESS(f'Removed old backup: {filename}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Failed to remove {filename}: {e}')
                        )
