"""
HR Wallet Tests Package

This package contains all test files for the HR Wallet application.

Test Categories:
- Unit Tests: Individual component testing
- Integration Tests: Testing component interactions
- End-to-End Tests: Full workflow testing
- Performance Tests: Load and performance testing
- API Tests: REST API endpoint testing
"""

# Test configuration
import os
import sys
import django
from django.conf import settings

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings for testing
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
    django.setup()