# Notification System Implementation

This document describes the backend implementation of the notification system for the Risk Assessment application.

## Overview

The notification system provides real-time notifications to users based on their role (Principal Investigator - PI or Study Director - SD) when assessment-related actions occur.

## Features

### 1. Notification Types

- **PI Submissions**: When a PI saves an assessment, SD gets notified
- **SD Submissions**: When an SD creates/saves an assessment, PI gets notified
- **SD Approvals**: When an SD approves an assessment, PI gets notified
- **SD Rejections**: When an SD rejects an assessment, PI gets notified

### 2. User Role-Based Notifications

- **Study Director (SD)**: Receives notifications about PI submissions
- **Principal Investigator (PI)**: Receives notifications about SD actions and SD-created assessments

### 3. Notification Management

- Mark individual notifications as read
- Mark all notifications as read
- Track unread notification count
- Retrieve notifications with study information

## Database Schema

### Table: `assessment_notifications`

```sql
CREATE TABLE "Risk Assessment".assessment_notifications (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    action_by_name VARCHAR(255) NOT NULL,
    action_by_email VARCHAR(255) NOT NULL,
    reason TEXT NOT NULL,
    comments TEXT,
    target_user_type VARCHAR(10) NOT NULL CHECK (target_user_type IN ('PI', 'SD')),
    study_id INTEGER NOT NULL,
    action_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_status BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

- `idx_assessment_notifications_assessment_id`
- `idx_assessment_notifications_target_user_type`
- `idx_assessment_notifications_study_id`
- `idx_assessment_notifications_read_status`
- `idx_assessment_notifications_action_date`

## API Endpoints

### 1. Get Notifications
```
GET /api/v1/notifications?user_type={PI|SD}
```
Returns notifications for the specified user type with unread count.

### 2. Mark Notification as Read
```
PUT /api/v1/notifications/{notification_id}/read
```
Marks a specific notification as read.

### 3. Mark All Notifications as Read
```
PUT /api/v1/notifications/mark-all-read
```
Marks all notifications as read for a user type.

### 4. Get Unread Count
```
GET /api/v1/notifications/unread-count?user_type={PI|SD}
```
Returns the count of unread notifications.

## Implementation Details

### Files Created/Modified

1. **Schema**: `schema/notification_schema.py`
   - Defines Pydantic models for notifications
   - Includes `AssessmentNotification`, `NotificationResponse`, etc.

2. **Service**: `services/notification_service.py`
   - Business logic for notification operations
   - Methods for creating, retrieving, and updating notifications

3. **Router**: `api/v1/endpoints/notification_router.py`
   - API endpoints for notification operations
   - Handles authentication and validation

4. **Assessment Service**: `services/assessment_service.py`
   - Modified to create notifications when assessments are saved
   - Integrated notification creation in save workflow

5. **Assessment Router**: `api/v1/endpoints/assessment_router.py`
   - Modified to create notifications on approval/rejection
   - Integrated notification creation in approval workflow

6. **Main App**: `main.py`
   - Added notification router to FastAPI app

7. **Database**: `database/migrations/create_notifications_table.sql`
   - SQL migration to create notifications table
   - Includes indexes and constraints

8. **Migration Script**: `run_migration.py`
   - Python script to execute the database migration

### Integration Points

#### 1. Assessment Save (Dynamic Target Based on Submitter)
When an assessment is saved, the target user type is determined dynamically:
```python
# In assessment_service.py save_assessment method
# First determine user type based on study information
user_type_result = db.execute_query(study_user_query, [user_email, user_email, study_id])
user_type = user_type_result[0]['user_type'] if user_type_result else 'PI'

# Create notification with dynamic target
notification_result = notification_service.create_assessment_submission_notification(
    assessment_id=assessment_id,
    study_id=study_id,
    submitter_name=user_name,
    submitter_email=user_email,
    submitter_type=user_type  # 'PI' or 'SD'
)
```

**Target User Type Logic:**
- If **PI submits** → Target is **SD** (SD gets "Initial Save" notification)
- If **SD submits** → Target is **PI** (PI gets "SD Created" notification)

#### 2. Assessment Approval (SD → PI Notification)
When an SD approves an assessment:
```python
# In assessment_router.py approve_assessment method
notification_result = notification_service.create_assessment_approval_notification(
    assessment_id=assessment_id,
    study_id=assessment['study_id'],
    sd_name=request.action_by_name,
    sd_email=request.action_by_email,
    pi_name=pi_name,
    pi_email=pi_email,
    action="Approved",
    reason=request.reason,
    comments=request.comments
)
```

#### 3. Assessment Rejection (SD → PI Notification)
When an SD rejects an assessment:
```python
# In assessment_router.py reject_assessment method
notification_result = notification_service.create_assessment_approval_notification(
    assessment_id=assessment_id,
    study_id=assessment['study_id'],
    sd_name=request.action_by_name,
    sd_email=request.action_by_email,
    pi_name=pi_name,
    pi_email=pi_email,
    action="Rejected",
    reason=request.reason,
    comments=request.comments
)
```

## Setup Instructions

### 1. Run Database Migration
```bash
python run_migration.py
```

### 2. Start the Backend Server
```bash
python main.py
```

### 3. Test the API Endpoints
```bash
# Get notifications for SD
curl -X GET "http://localhost:8000/api/v1/notifications?user_type=SD" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get notifications for PI
curl -X GET "http://localhost:8000/api/v1/notifications?user_type=PI" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Mark notification as read
curl -X PUT "http://localhost:8000/api/v1/notifications/1/read" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Mark all notifications as read
curl -X PUT "http://localhost:8000/api/v1/notifications/mark-all-read" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"user_type": "PI"}'
```

## Error Handling

- Notification creation failures don't affect the main assessment workflow
- All notification operations are wrapped in try-catch blocks
- Logging is implemented for debugging and monitoring
- Graceful degradation when notification system is unavailable

## Future Enhancements

1. **Email Notifications**: Send email notifications in addition to in-app notifications
2. **Real-time Updates**: Implement WebSocket connections for real-time notifications
3. **Notification Preferences**: Allow users to configure notification preferences
4. **Bulk Operations**: Support for bulk notification operations
5. **Notification Templates**: Configurable notification message templates
6. **Advanced Filtering**: Filter notifications by date range, action type, or study

## Testing

The notification system includes comprehensive error handling and logging. Test scenarios:

1. **PI Submission Flow**: PI saves assessment → SD receives "Initial Save" notification
2. **SD Submission Flow**: SD creates assessment → PI receives "SD Created" notification
3. **Approval Flow**: SD approves assessment → PI receives "Approved" notification
4. **Rejection Flow**: SD rejects assessment → PI receives "Rejected" notification
5. **User Type Detection**: System correctly identifies PI vs SD based on study data
6. **Error Handling**: Notification creation fails → Assessment workflow continues
7. **Database Errors**: Database connection issues → Graceful error handling

## Monitoring

Monitor the following logs for notification system health:
- Notification creation success/failure
- Database connection issues
- API endpoint performance
- Error rates and types 