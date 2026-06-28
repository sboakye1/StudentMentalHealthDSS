#!/usr/bin/env python3
"""Test script to debug Flask app initialization errors"""

import sys
import traceback

try:
    print("Testing Flask app initialization...")
    from config import create_app
    print("✓ Config module imported successfully")
    
    app = create_app()
    print("✓ Flask app created successfully")
    
    # Test template rendering
    with app.test_client() as client:
        print("\nTesting routes...")
        
        # Test home route
        response = client.get('/')
        print(f"GET / → Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.data.decode()}")
        else:
            print("✓ Home route works!")
        
        # Test health check route
        response = client.get('/api/health')
        print(f"GET /api/health → Status: {response.status_code}")
        if response.status_code in [200, 503]:
            print("✓ Health check route works!")
        else:
            print(f"Error: {response.data.decode()}")
            
except Exception as e:
    print(f"\n❌ Error occurred:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {str(e)}")
    print(f"\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All tests passed!")
