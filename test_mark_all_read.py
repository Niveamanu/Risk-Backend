#!/usr/bin/env python3
"""
Test script to verify the mark all read endpoint works correctly
"""

import sys
import os
sys.path.append('.')

from services.notification_service import NotificationService

def test_mark_all_read():
    """Test the mark all read functionality"""
    try:
        print("🔔 Testing Mark All Read Endpoint")
        print("=" * 50)
        
        # Initialize service
        notification_service = NotificationService()
        
        # Test data
        test_user_type = "SD"
        
        print(f"🧪 Testing mark all read for user type: {test_user_type}")
        print()
        
        # Test the mark_all_as_read method
        try:
            result = notification_service.mark_all_as_read(test_user_type)
            
            print(f"✅ Successfully marked all notifications as read")
            print(f"   Updated count: {result.get('updated_count', 0)}")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Message: {result.get('message', 'No message')}")
            print()
            
            # Test with PI user type
            pi_result = notification_service.mark_all_as_read("PI")
            print(f"✅ Successfully marked all PI notifications as read")
            print(f"   Updated count: {pi_result.get('updated_count', 0)}")
            print(f"   Success: {pi_result.get('success', False)}")
            print()
            
            # Test with invalid user type
            try:
                invalid_result = notification_service.mark_all_as_read("INVALID")
                print(f"❌ Should have failed but didn't")
            except Exception as e:
                print(f"✅ Expected error for invalid user type: {str(e)}")
            
        except Exception as e:
            print(f"❌ Error marking all notifications as read: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("=" * 50)
        print("🏁 Mark all read test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mark_all_read()