#!/usr/bin/env python3
"""Debug test for Flask app"""
import os
import sys

# Set the working directory
os.chdir(r'c:\Users\hp\Desktop\StudentMentalHealthDSS')
sys.path.insert(0, os.getcwd())

try:
    print("=" * 60)
    print("Testing Flask app...")
    print("=" * 60)
    print(f"Current directory: {os.getcwd()}")
    print(f"Templates folder: {os.path.exists('templates')}")
    print(f"Static folder: {os.path.exists('static')}")
    print()
    
    from config import create_app
    print("✓ Config module imported")
    
    app = create_app()
    print("✓ Flask app created")
    print(f"  Template folder: {app.template_folder}")
    print(f"  Static folder: {app.static_folder}")
    print()
    
    print("Testing route rendering...")
    with app.test_client() as client:
        response = client.get('/')
        print(f"GET / → Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ SUCCESS - Template loaded!")
            # Show first part of response
            data = response.data.decode('utf-8')
            print(f"Response length: {len(data)} bytes")
            print("First 300 chars:")
            print(data[:300])
        else:
            print(f"✗ ERROR - Status {response.status_code}")
            print(f"Response: {response.data.decode('utf-8')[:500]}")
            
except Exception as e:
    print("=" * 60)
    print("EXCEPTION OCCURRED:")
    print("=" * 60)
    import traceback
    traceback.print_exc()
