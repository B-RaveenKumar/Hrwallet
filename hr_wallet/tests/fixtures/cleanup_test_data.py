#!/usr/bin/env python
"""
Database Cleanup Script - Remove Test Users and Associated Data
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

from django.contrib.auth import get_user_model
from core_hr.models import Employee, Company, Department, Attendance, LeaveRequest, Payroll, LeaveBalance, WorkHours
from django.db import transaction

User = get_user_model()

def cleanup_test_data():
    """Remove all test users and their associated data"""
    print("🧹 CLEANING UP TEST DATA")
    print("=" * 50)
    
    # Test users to remove
    test_usernames = ['testadmin', 'hrmanager', 'employee']
    
    with transaction.atomic():
        print("\n1️⃣ Identifying test users to remove:")
        test_users = []
        for username in test_usernames:
            try:
                user = User.objects.get(username=username)
                test_users.append(user)
                print(f"   ✅ Found: {username} ({user.role})")
            except User.DoesNotExist:
                print(f"   ⚠️  Not found: {username}")
        
        if not test_users:
            print("   ℹ️  No test users found to remove")
            return
        
        print(f"\n2️⃣ Removing {len(test_users)} test users and associated data:")
        
        for user in test_users:
            print(f"\n   🗑️  Removing user: {user.username}")
            
            # Remove associated Employee profile if exists
            try:
                employee = user.employee
                print(f"      - Employee profile: {employee.employee_id}")
                
                # Remove related data
                attendance_count = Attendance.objects.filter(employee=employee).count()
                if attendance_count > 0:
                    Attendance.objects.filter(employee=employee).delete()
                    print(f"      - Removed {attendance_count} attendance records")
                
                leave_requests_count = LeaveRequest.objects.filter(employee=employee).count()
                if leave_requests_count > 0:
                    LeaveRequest.objects.filter(employee=employee).delete()
                    print(f"      - Removed {leave_requests_count} leave requests")
                
                payroll_count = Payroll.objects.filter(employee=employee).count()
                if payroll_count > 0:
                    Payroll.objects.filter(employee=employee).delete()
                    print(f"      - Removed {payroll_count} payroll records")
                
                work_hours_count = WorkHours.objects.filter(employee=employee).count()
                if work_hours_count > 0:
                    WorkHours.objects.filter(employee=employee).delete()
                    print(f"      - Removed {work_hours_count} work hours records")
                
                try:
                    leave_balance = employee.leavebalance
                    leave_balance.delete()
                    print(f"      - Removed leave balance")
                except:
                    pass
                
                # Remove employee profile
                employee.delete()
                print(f"      - Removed employee profile")
                
            except Employee.DoesNotExist:
                print(f"      - No employee profile found")
            
            # Remove user account
            user.delete()
            print(f"      ✅ User {user.username} removed successfully")
        
        print(f"\n3️⃣ Database state after cleanup:")
        remaining_users = User.objects.count()
        remaining_employees = Employee.objects.count()
        companies = Company.objects.count()
        departments = Department.objects.count()
        
        print(f"   - Users remaining: {remaining_users}")
        print(f"   - Employees remaining: {remaining_employees}")
        print(f"   - Companies: {companies}")
        print(f"   - Departments: {departments}")
        
        print(f"\n✅ Test data cleanup completed successfully!")
        
        # Show remaining users
        print(f"\n4️⃣ Remaining users in database:")
        for user in User.objects.all():
            has_employee = hasattr(user, 'employee')
            employee_id = user.employee.employee_id if has_employee else "No profile"
            print(f"   - {user.username} ({user.role}) - Employee: {employee_id}")

if __name__ == '__main__':
    cleanup_test_data()
