# HR Wallet Tests

This directory contains all test files for the HR Wallet application.

## Test Files Overview

### Unit Tests
- `test_profile_creation.py` - Employee profile creation tests
- `test_employee_api.py` - Employee API endpoint tests
- `test_currency_conversion.py` - Currency conversion functionality tests
- `test_template_syntax.py` - Template syntax validation tests

### Integration Tests
- `test_profile_creation_workflow.py` - Complete profile creation workflow
- `test_navigation_changes.py` - Navigation system tests
- `test_payroll_http.py` - Payroll HTTP request tests

### End-to-End Tests
- `comprehensive_test.py` - Comprehensive system tests
- `comprehensive_test_final.py` - Final comprehensive tests
- `comprehensive_500_error_test.py` - Error handling tests
- `final_comprehensive_test.py` - Final system validation
- `final_test.py` - Final test suite

### Server Tests
- `test_server.py` - Server functionality tests

### Test Data Management
- `setup_test_data.py` - Test data setup utilities
- `cleanup_test_data.py` - Test data cleanup utilities

### Static Files
- `test_bootstrap_fix.html` - Bootstrap CSS/JS testing template

## Running Tests

```bash
# Run all tests
python manage.py test tests

# Run specific test file
python -m pytest tests/test_profile_creation.py

# Run with coverage
python -m pytest tests/ --cov=.
```

## Test Database

Tests use a separate test database that is created and destroyed automatically.
Test data is isolated and doesn't affect the production database.

## Notes

- All test files have been moved from the main project directory
- Tests are organized by functionality and scope
- Use Django's testing framework for database-related tests
- Use pytest for utility and API tests