from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, Any
from core.auth_middleware import require_auth
from services.notification_service import notification_service
from schema.notification_schema import NotificationResponse, MarkAsReadRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/notifications", response_model=NotificationResponse)
async def get_notifications(
    user_type: str = Query(..., description="User type: 'PI' or 'SD'"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get notifications for the current user based on their role
    """
    try:
        logger.info(f"Getting notifications for user type: {user_type}")
        logger.info(f"Current user: {current_user}")
        
        # Validate user type
        if user_type.upper() not in ['PI', 'SD']:
            raise HTTPException(status_code=400, detail="user_type must be 'PI' or 'SD'")
        
        user_email = current_user.get("email", "")
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found in token")
        user_email = user_email.lower()  # Convert to lowercase for consistent comparison
        
        result = notification_service.get_notifications(user_type.upper(), user_email)
        logger.info(f"Retrieved {len(result.notifications)} notifications, {result.unread_count} unread")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")

@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Mark a specific notification as read
    """
    try:
        logger.info(f"Marking notification {notification_id} as read")
        
        result = notification_service.mark_as_read(notification_id)
        logger.info(f"Successfully marked notification {notification_id} as read")
        
        return result
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")

@router.put("/notifications/mark-all-read")
async def mark_all_notifications_as_read(
    user_type: str = Query(..., description="User type: 'PI' or 'SD'"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Mark all notifications as read for a specific user type
    """
    try:
        logger.info(f"Marking all notifications as read for user type: {user_type}")
        
        # Validate user type
        if user_type.upper() not in ['PI', 'SD']:
            raise HTTPException(status_code=400, detail="user_type must be 'PI' or 'SD'")
        
        result = notification_service.mark_all_as_read(user_type.upper())
        logger.info(f"Successfully marked {result.get('updated_count', 0)} notifications as read")
        
        return result
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark all notifications as read: {str(e)}")

@router.get("/notifications/unread-count")
async def get_unread_count(
    user_type: str = Query(..., description="User type: 'PI' or 'SD'"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get the count of unread notifications for a user type
    """
    try:
        logger.info(f"Getting unread count for user type: {user_type}")
        
        # Validate user type
        if user_type.upper() not in ['PI', 'SD']:
            raise HTTPException(status_code=400, detail="user_type must be 'PI' or 'SD'")
        
        user_email = current_user.get("email", "")
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found in token")
        user_email = user_email.lower()  # Convert to lowercase for consistent comparison
        
        result = notification_service.get_unread_count(user_type.upper(), user_email)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get unread count: {str(e)}")

# Test endpoint to verify router is working
@router.get("/test")
async def test_endpoint():
    """
    Test endpoint to verify the notification router is working
    """
    return {"message": "Notification router is working!", "status": "success"} 