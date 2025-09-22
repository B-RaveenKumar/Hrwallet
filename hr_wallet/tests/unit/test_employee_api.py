"""
Simple test to verify the employee API endpoint is working
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('d:\\VISHNRX\\SM Product\\hr_wallet')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from core_hr.models import Employee

def test_employee_api():
    """Test if the employee detail API works"""
    client = Client()
    
    # Try to get a user and create a test scenario
    User = get_user_model()
    users = User.objects.all()[:1]
    
    if users:
        user = users[0]
        print(f"Testing with user: {user.username}")
        
        # Try to get employees for this user's company
        employees = Employee.objects.filter(company=user.company)[:1]
        
        if employees:
            employee = employees[0]
            print(f"Testing employee API with employee ID: {employee.id}")
            
            # Simulate login
            client.force_login(user)
            
            # Test the API endpoint
            response = client.get(f'/api/employees/{employee.id}/')
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ API endpoint working correctly!")
                print("Response content:", response.json())
            else:
                print("❌ API endpoint failed!")
                print("Response content:", response.content.decode())
        else:
            print("No employees found to test")
    else:
        print("No users found to test")

if __name__ == "__main__":
    test_employee_api()