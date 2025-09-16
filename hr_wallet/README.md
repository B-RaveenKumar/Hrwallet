# HR Wallet - Human Resources Management System

A comprehensive, role-based Human Resources Management System built with Django, featuring secure authentication, role-based access control (RBAC), and modern responsive design.

## 🎯 Features

### 🔐 Role-Based Access Control (RBAC)
- **Super Administrator**: Complete system control, HR Manager management, system settings
- **HR Manager**: Employee management, leave approvals, payroll oversight, HR analytics
- **Employee**: Self-service portal, profile management, attendance tracking, leave requests

### 🏗️ Core Functionality
- **User Authentication**: Secure login/logout with session management
- **Employee Management**: Complete employee lifecycle management
- **Department Management**: Organizational structure management
- **Attendance Tracking**: Clock in/out, attendance reports
- **Leave Management**: Leave requests, approvals, balance tracking
- **Audit Logging**: Security event tracking and monitoring

### 🎨 Modern UI/UX
- **Responsive Design**: Bootstrap 5 with mobile-first approach
- **Role-Specific Dashboards**: Tailored interfaces for each user role
- **Professional Styling**: Modern cards, gradients, and animations
- **Intuitive Navigation**: Role-appropriate menu structures

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation & Setup

1. **Clone or Download** the HR Wallet folder
2. **Navigate** to the hr_wallet directory
3. **Run the setup script**:

#### Windows:
```bash
start.bat
```

#### Linux/Mac:
```bash
chmod +x start.sh
./start.sh
```

#### Manual Setup:
```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py makemigrations
python manage.py migrate

# Create sample data
python setup_database.py

# Start server
python manage.py runserver 127.0.0.1:8000
```

## 🌐 Access the Application

Open your browser and go to: **http://127.0.0.1:8000**

## 🔑 Login Credentials

| Role | Username | Password | Dashboard URL |
|------|----------|----------|---------------|
| **Super Admin** | admin | admin123 | `/admin-panel/` |
| **HR Manager** | sarah.johnson | password123 | `/hr-dashboard/` |
| **Employee** | john.doe | password123 | `/employee-portal/` |

## 📁 Project Structure

```
hr_wallet/
├── hr_wallet/              # Django project settings
│   ├── settings.py         # Main configuration
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI configuration
├── accounts/              # User authentication & RBAC
│   ├── models.py          # Custom User model
│   ├── views.py           # Authentication views
│   ├── decorators.py      # Security decorators
│   └── middleware.py      # Security middleware
├── core_hr/               # Core HR functionality
│   ├── models.py          # Employee, Department, etc.
│   └── admin.py           # Django admin configuration
├── admin_panel/           # Super Admin interface
├── hr_dashboard/          # HR Manager interface
├── employee_portal/       # Employee self-service
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── accounts/          # Authentication templates
│   ├── admin_panel/       # Admin templates
│   ├── hr_dashboard/      # HR templates
│   └── employee_portal/   # Employee templates
├── static/                # Static files (CSS, JS, images)
├── requirements.txt       # Python dependencies
├── manage.py             # Django management script
├── setup_database.py     # Database initialization
├── start.bat             # Windows startup script
├── start.sh              # Linux/Mac startup script
└── README.md             # This file
```

## 🛡️ Security Features

### Authentication & Authorization
- Custom User model with role-based permissions
- Session-based authentication with security enhancements
- CSRF protection on all forms
- Secure password validation

### Role-Based Access Control
- **URL-level security**: Middleware enforces role-based URL access
- **View-level security**: Decorators protect individual views
- **Template-level security**: Conditional content based on user role
- **Data isolation**: Users only see data appropriate to their role

### Audit & Monitoring
- Security event logging
- Failed access attempt tracking
- User action audit trail
- Session security monitoring

## 🔧 Customization

### Adding New Users
1. Access Django Admin: http://127.0.0.1:8000/admin/
2. Login with super admin credentials
3. Navigate to Users section
4. Add new user with appropriate role

### Modifying Roles
Edit `accounts/models.py` to modify the `ROLE_CHOICES` and related permissions.

### Adding New Features
1. Create new Django apps for additional functionality
2. Add to `INSTALLED_APPS` in `settings.py`
3. Create models, views, and templates
4. Update URL routing

## 📊 Database Models

### User Model
- Extended Django User with role field
- Security fields for audit tracking
- Role-based property methods

### Core HR Models
- **Company**: Organization information
- **Department**: Organizational structure
- **Employee**: Employee profiles and details
- **Attendance**: Time tracking and attendance records
- **LeaveRequest**: Leave management system

## 🎨 UI Components

### Dashboard Features
- **Statistics Cards**: Key metrics and KPIs
- **Quick Actions**: Common task shortcuts
- **Recent Activity**: Timeline of recent events
- **Navigation**: Role-specific menu structures

### Responsive Design
- Mobile-first Bootstrap 5 framework
- Adaptive layouts for all screen sizes
- Touch-friendly interface elements
- Professional color schemes per role

## 🚀 Production Deployment

### Environment Variables
```bash
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=your-database-url
```

### Security Checklist
- [ ] Change default passwords
- [ ] Set strong SECRET_KEY
- [ ] Configure HTTPS/SSL
- [ ] Set up proper database
- [ ] Configure email backend
- [ ] Enable security middleware
- [ ] Set up monitoring and logging

## 🤝 Support

For issues, questions, or contributions:
1. Check the Django documentation
2. Review the code comments and docstrings
3. Test with the provided sample data
4. Verify role-based access control is working

## 📄 License

This project is created for demonstration purposes. Modify and use according to your needs.

---

**HR Wallet** - Comprehensive Human Resources Management System with Role-Based Access Control
