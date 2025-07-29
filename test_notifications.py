#!/usr/bin/env python3
"""
Test script for the notification system
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
TEST_TOKEN = "your_test_token_here"  # Replace with actual test token
HEADERS = {
    "Authorization": f"Bearer {TEST_TOKEN}",
    "Content-Type": "application/json"
}

def test_get_notifications(user_type):
    """Test getting notifications for a user type"""
    print(f"\n=== Testing Get Notifications for {user_type} ===")
    
    try:
        response = requests.get(
            f"{API_BASE}/notifications",
            params={"user_type": user_type},
            headers=HEADERS
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully retrieved notifications")
            print(f"  - Total notifications: {len(data.get('notifications', []))}")
            print(f"  - Unread count: {data.get('unread_count', 0)}")
            
            # Print first few notifications
            notifications = data.get('notifications', [])
            for i, notification in enumerate(notifications[:3]):
                print(f"  Notification {i+1}:")
                print(f"    - ID: {notification.get('id')}")
                print(f"    - Action: {notification.get('action')}")
                print(f"    - Assessment ID: {notification.get('assessment_id')}")
                print(f"    - Read: {notification.get('read')}")
        else:
            print(f"✗ Failed to get notifications: {response.text}")
            
    except Exception as e:
        print(f"✗ Error testing get notifications: {e}")

def test_mark_as_read(notification_id):
    """Test marking a notification as read"""
    print(f"\n=== Testing Mark as Read for Notification {notification_id} ===")
    
    try:
        response = requests.put(
            f"{API_BASE}/notifications/{notification_id}/read",
            headers=HEADERS
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully marked notification as read")
            print(f"  - Message: {data.get('message')}")
        else:
            print(f"✗ Failed to mark notification as read: {response.text}")
            
    except Exception as e:
        print(f"✗ Error testing mark as read: {e}")

def test_mark_all_as_read(user_type):
    """Test marking all notifications as read"""
    print(f"\n=== Testing Mark All as Read for {user_type} ===")
    
    try:
        response = requests.put(
            f"{API_BASE}/notifications/mark-all-read",
            headers=HEADERS,
            json={"user_type": user_type}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully marked all notifications as read")
            print(f"  - Message: {data.get('message')}")
            print(f"  - Updated count: {data.get('updated_count', 0)}")
        else:
            print(f"✗ Failed to mark all notifications as read: {response.text}")
            
    except Exception as e:
        print(f"✗ Error testing mark all as read: {e}")

def test_unread_count(user_type):
    """Test getting unread count"""
    print(f"\n=== Testing Unread Count for {user_type} ===")
    
    try:
        response = requests.get(
            f"{API_BASE}/notifications/unread-count",
            params={"user_type": user_type},
            headers=HEADERS
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully retrieved unread count")
            print(f"  - Unread count: {data.get('unread_count', 0)}")
            print(f"  - User type: {data.get('user_type')}")
        else:
            print(f"✗ Failed to get unread count: {response.text}")
            
    except Exception as e:
        print(f"✗ Error testing unread count: {e}")

def test_notification_router():
    """Test the notification router test endpoint"""
    print(f"\n=== Testing Notification Router ===")
    
    try:
        response = requests.get(f"{API_BASE}/test")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Notification router is working")
            print(f"  - Message: {data.get('message')}")
            print(f"  - Status: {data.get('status')}")
        else:
            print(f"✗ Notification router test failed: {response.text}")
            
    except Exception as e:
        print(f"✗ Error testing notification router: {e}")

def run_all_tests():
    """Run all notification system tests"""
    print("🚀 Starting Notification System Tests")
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Test notification router
    test_notification_router()
    
    # Test for both user types
    for user_type in ['PI', 'SD']:
        # Get notifications
        test_get_notifications(user_type)
        
        # Get unread count
        test_unread_count(user_type)
        
        # Mark all as read
        test_mark_all_as_read(user_type)
        
        # Get notifications again to verify
        test_get_notifications(user_type)
    
    # Test individual mark as read (if notifications exist)
    test_mark_as_read(1)
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    print("⚠️  IMPORTANT: Make sure to:")
    print("   1. Update TEST_TOKEN with a valid authentication token")
    print("   2. Ensure the backend server is running on localhost:8000")
    print("   3. Run the database migration: python run_migration.py")
    print()
    
    # Uncomment the line below to run tests
    # run_all_tests()
    
    print("🔧 To run tests, uncomment the run_all_tests() call in this script") 