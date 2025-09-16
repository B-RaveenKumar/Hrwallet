#!/bin/bash

echo "========================================"
echo "    HR Wallet - Setup and Start"
echo "========================================"
echo

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo
echo "🗄️  Setting up database..."
python manage.py makemigrations
python manage.py migrate

echo
echo "👥 Creating sample data..."
python setup_database.py

echo
echo "🚀 Starting HR Wallet server..."
echo
echo "🌐 Access the application at: http://127.0.0.1:8000"
echo
echo "📋 Login Credentials:"
echo "  Super Admin: admin / admin123"
echo "  HR Manager: sarah.johnson / password123"  
echo "  Employee: john.doe / password123"
echo
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo

python manage.py runserver 127.0.0.1:8000
