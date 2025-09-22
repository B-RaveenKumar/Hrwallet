#!/usr/bin/env python
"""
HR Wallet Test Runner

This script provides convenient commands to run different types of tests.

Usage:
    python run_tests.py unit          # Run unit tests only
    python run_tests.py integration   # Run integration tests only
    python run_tests.py e2e           # Run end-to-end tests only
    python run_tests.py all           # Run all tests
    python run_tests.py coverage      # Run all tests with coverage
"""

import os
import sys
import subprocess
import argparse

def run_command(command):
    """Run a shell command and return the result"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    return result.returncode == 0

def run_unit_tests():
    """Run unit tests"""
    return run_command("python -m pytest tests/unit/ -v")

def run_integration_tests():
    """Run integration tests"""
    return run_command("python -m pytest tests/integration/ -v")

def run_e2e_tests():
    """Run end-to-end tests"""
    return run_command("python -m pytest tests/e2e/ -v")

def run_all_tests():
    """Run all tests"""
    return run_command("python -m pytest tests/ -v")

def run_with_coverage():
    """Run all tests with coverage report"""
    commands = [
        "pip install coverage pytest-cov",
        "python -m pytest tests/ --cov=. --cov-report=html --cov-report=term"
    ]
    for cmd in commands:
        if not run_command(cmd):
            return False
    return True

def main():
    parser = argparse.ArgumentParser(description="HR Wallet Test Runner")
    parser.add_argument("test_type", 
                       choices=["unit", "integration", "e2e", "all", "coverage"],
                       help="Type of tests to run")
    
    args = parser.parse_args()
    
    # Set up environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
    
    # Run the appropriate tests
    success = False
    if args.test_type == "unit":
        success = run_unit_tests()
    elif args.test_type == "integration":
        success = run_integration_tests()
    elif args.test_type == "e2e":
        success = run_e2e_tests()
    elif args.test_type == "all":
        success = run_all_tests()
    elif args.test_type == "coverage":
        success = run_with_coverage()
    
    if success:
        print("\n✅ Tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()