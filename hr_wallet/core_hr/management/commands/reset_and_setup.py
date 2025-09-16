from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Reset database and setup fresh HR Wallet system with multi-company support'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to reset the database (THIS WILL DELETE ALL DATA)',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  WARNING: This command will DELETE ALL DATA in the database!\n'
                    'This will:\n'
                    '  - Delete the current database file\n'
                    '  - Remove all migration files (except initial)\n'
                    '  - Create fresh migrations\n'
                    '  - Set up a clean multi-company system\n\n'
                    'To proceed, run: python manage.py reset_and_setup --confirm'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('🚀 Starting fresh HR Wallet setup...'))

        try:
            # Step 1: Remove database file
            db_path = settings.DATABASES['default']['NAME']
            if os.path.exists(db_path):
                os.remove(db_path)
                self.stdout.write('  ✓ Removed existing database')

            # Step 2: Remove migration files (keep __init__.py and 0001_initial.py)
            self.cleanup_migrations()

            # Step 3: Create fresh migrations
            self.stdout.write('  📝 Creating fresh migrations...')
            call_command('makemigrations', verbosity=0)
            self.stdout.write('  ✓ Created fresh migrations')

            # Step 4: Apply migrations
            self.stdout.write('  🔧 Applying migrations...')
            call_command('migrate', verbosity=0)
            self.stdout.write('  ✓ Applied migrations successfully')

            # Step 5: Create demo company
            self.stdout.write('  🏢 Setting up demo company...')
            call_command('setup_demo_company', '--company-name=Demo Tech Solutions', '--company-code=DEMO')

            self.stdout.write(
                self.style.SUCCESS(
                    '\n🎉 HR Wallet system setup completed successfully!\n\n'
                    '🌐 Access your system:\n'
                    '  URL: http://127.0.0.1:8000/\n'
                    '  1. Select "Demo Tech Solutions" from company selection\n'
                    '  2. Login with demo credentials\n\n'
                    '👤 Demo Users:\n'
                    '  Super Admin: admin / admin123\n'
                    '  HR Manager: hr.manager / password123\n'
                    '  Employee: john.doe / password123\n\n'
                    '🚀 Start the server: python manage.py runserver'
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error during setup: {str(e)}'))
            raise

    def cleanup_migrations(self):
        """Remove problematic migration files"""
        apps_to_clean = ['accounts', 'core_hr']
        
        for app in apps_to_clean:
            migrations_dir = f'{app}/migrations'
            if os.path.exists(migrations_dir):
                for filename in os.listdir(migrations_dir):
                    if filename.endswith('.py') and filename not in ['__init__.py', '0001_initial.py']:
                        file_path = os.path.join(migrations_dir, filename)
                        os.remove(file_path)
                        self.stdout.write(f'  ✓ Removed {file_path}')
                
                # Clean __pycache__
                pycache_dir = os.path.join(migrations_dir, '__pycache__')
                if os.path.exists(pycache_dir):
                    import shutil
                    shutil.rmtree(pycache_dir)
                    self.stdout.write(f'  ✓ Cleaned {pycache_dir}')
