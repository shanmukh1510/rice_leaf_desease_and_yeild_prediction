#!/usr/bin/env python3
"""
RiceAI Diagnostic Test Script
Run this to check if everything is set up correctly
"""

import os
import sys
import sqlite3

print("=" * 60)
print("🌾 RiceAI System Diagnostic Test")
print("=" * 60)
print()

# Test 1: Python Version
print("✓ Test 1: Python Version")
print(f"  Python {sys.version}")
if sys.version_info >= (3, 8):
    print("  ✅ PASS - Python version is 3.8 or higher")
else:
    print("  ❌ FAIL - Please upgrade to Python 3.8 or higher")
print()

# Test 2: Required Files
print("✓ Test 2: Required Files")
required_files = {
    'app.py': 'Main application',
    'requirements.txt': 'Dependencies',
    'templates/signup.html': 'Signup template',
    'templates/login.html': 'Login template',
    'templates/home.html': 'Home template',
    'static/css/style.css': 'Stylesheet',
    'static/js/main.js': 'JavaScript'
}

all_files_exist = True
for file, description in required_files.items():
    if os.path.exists(file):
        print(f"  ✅ {file} - {description}")
    else:
        print(f"  ❌ {file} - MISSING!")
        all_files_exist = False

if all_files_exist:
    print("  ✅ PASS - All required files present")
else:
    print("  ❌ FAIL - Some files are missing")
print()

# Test 3: Python Packages
print("✓ Test 3: Required Python Packages")
required_packages = [
    'flask',
    'werkzeug',
    'numpy',
    'pandas'
]

all_packages_installed = True
for package in required_packages:
    try:
        __import__(package)
        print(f"  ✅ {package}")
    except ImportError:
        print(f"  ❌ {package} - NOT INSTALLED")
        all_packages_installed = False

if all_packages_installed:
    print("  ✅ PASS - All packages installed")
else:
    print("  ❌ FAIL - Run: pip install -r requirements.txt")
print()

# Test 4: Database Setup
print("✓ Test 4: Database")
if os.path.exists('rice_farming.db'):
    print("  ✅ Database file exists")
    try:
        conn = sqlite3.connect('rice_farming.db')
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            print("  ✅ Users table exists")
            
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            print(f"  ℹ️  Current users: {count}")
        else:
            print("  ❌ Users table missing")
        
        # Check predictions table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
        if cursor.fetchone():
            print("  ✅ Predictions table exists")
        else:
            print("  ❌ Predictions table missing")
        
        conn.close()
        print("  ✅ PASS - Database is accessible")
    except Exception as e:
        print(f"  ❌ FAIL - Database error: {e}")
else:
    print("  ⚠️  Database doesn't exist yet")
    print("  ℹ️  It will be created when you run the app")
print()

# Test 5: Create Test User
print("✓ Test 5: Test User Creation")
try:
    # Import here to test imports work
    from werkzeug.security import generate_password_hash
    
    # Try to create database if it doesn't exist
    conn = sqlite3.connect('rice_farming.db')
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            prediction_type TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    
    # Check if test user already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('testuser_diagnostic',))
    if cursor.fetchone():
        print("  ℹ️  Test user already exists (from previous test)")
        cursor.execute('DELETE FROM users WHERE username = ?', ('testuser_diagnostic',))
        conn.commit()
        print("  ✅ Deleted old test user")
    
    # Try to create test user
    test_username = 'testuser_diagnostic'
    test_email = 'test_diagnostic@example.com'
    test_password = generate_password_hash('testpass123')
    
    cursor.execute(
        'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
        (test_username, test_email, test_password)
    )
    conn.commit()
    print("  ✅ Test user created successfully")
    
    # Verify
    cursor.execute('SELECT id, username, email FROM users WHERE username = ?', (test_username,))
    user = cursor.fetchone()
    if user:
        print(f"  ✅ Verified - User ID: {user[0]}, Username: {user[1]}")
        
        # Clean up test user
        cursor.execute('DELETE FROM users WHERE username = ?', (test_username,))
        conn.commit()
        print("  ✅ Test user cleaned up")
    
    conn.close()
    print("  ✅ PASS - User creation works!")
    
except Exception as e:
    print(f"  ❌ FAIL - Error: {e}")
    print(f"  ℹ️  This is the likely cause of signup issues!")
print()

# Summary
print("=" * 60)
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 60)
print()

issues_found = []

if sys.version_info < (3, 8):
    issues_found.append("Python version too old")

if not all_files_exist:
    issues_found.append("Missing required files")

if not all_packages_installed:
    issues_found.append("Missing Python packages")

if issues_found:
    print("❌ ISSUES FOUND:")
    for i, issue in enumerate(issues_found, 1):
        print(f"  {i}. {issue}")
    print()
    print("📋 RECOMMENDED ACTIONS:")
    if "Python version" in str(issues_found):
        print("  1. Upgrade to Python 3.8 or higher")
    if "Missing required files" in str(issues_found):
        print("  2. Re-download all project files")
    if "Missing Python packages" in str(issues_found):
        print("  3. Run: pip install -r requirements.txt")
else:
    print("✅ ALL TESTS PASSED!")
    print()
    print("Your system is ready. If signup still doesn't work:")
    print("  1. Make sure Flask app is running: python app.py")
    print("  2. Visit: http://127.0.0.1:5000/test-db")
    print("  3. Check browser console (F12) for JavaScript errors")
    print("  4. Try different browser or incognito mode")

print()
print("=" * 60)
print("For more help, see TROUBLESHOOTING.md")
print("=" * 60)