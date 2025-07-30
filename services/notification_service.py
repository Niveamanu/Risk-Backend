from typing import List, Dict, Any, Optional
from database.connection import db
from fastapi import HTTPException
import logging
from datetime import datetime
from schema.notification_schema import AssessmentNotification, NotificationResponse, StudyInfo, AssessmentInfo

logger = logging.getLogger(__name__)

# Schema name declaration
SCHEMA_NAME = "Risk Assessment"

class NotificationService:
    def __init__(self):
        self.schema_name = SCHEMA_NAME
    
    def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new notification record
        """
        try:
            # Extract data
            assessment_id = notification_data.get("assessment_id")
            action = notification_data.get("action")
            action_by_name = notification_data.get("action_by_name")
            action_by_email = notification_data.get("action_by_email")
            reason = notification_data.get("reason")
            comments = notification_data.get("comments")
            target_user_type = notification_data.get("target_user_type")
            study_id = notification_data.get("study_id")
            
            # Validate required fields
            if not all([assessment_id, action, action_by_name, action_by_email, reason, target_user_type, study_id]):
                raise HTTPException(status_code=400, detail="Missing required notification fields")
            
            # Insert notification record
            insert_query = f"""
                INSERT INTO "{self.schema_name}".assessment_notifications
                (assessment_id, action, action_by_name, action_by_email, reason, comments, 
                 target_user_type, study_id, action_date, read_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            current_time = datetime.now()
            params = [
                assessment_id, action, action_by_name, action_by_email, reason, comments,
                target_user_type, study_id, current_time, False
            ]
            
            # For INSERT with RETURNING, we need to fetch the result
            connection = db.get_connection()
            cursor = connection.cursor()
            try:
                cursor.execute(insert_query, params)
                result = cursor.fetchone()
                connection.commit()
                notification_id = result['id'] if result else None
                
                if not notification_id:
                    raise HTTPException(status_code=500, detail="Failed to create notification")
            finally:
                cursor.close()
            
            logger.info(f"Created notification {notification_id} for assessment {assessment_id}")
            
            return {
                "success": True,
                "notification_id": notification_id,
                "message": "Notification created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")
    
    def get_notifications(self, user_type: str, user_email: str) -> NotificationResponse:
        """
        Get notifications for a specific user type and email
        """
        try:
            # Get notifications based on user type
            if user_type.upper() == 'SD':
                # SD gets notifications about PI submissions and actions
                query = f"""
                    SELECT 
                        n.id,
                        n.assessment_id,
                        n.action,
                        n.action_by_name,
                        n.action_by_email,
                        n.reason,
                        n.comments,
                        n.action_date,
                        n.read_status,
                        s.id as study_id,
                        s.site,
                        s.sponsor,
                        s.protocol,
                        s.studytype as study_type,
                        s.studytypetext as study_type_text,
                        s.description,
                        s.status as study_status,
                        s.phase,
                        a.monitoring_schedule,
                        s.siteid,
                        s.studyid,
                        s.active,
                        s.principal_investigator,
                        s.principal_investigator_email,
                        s.site_director,
                        s.site_director_email,
                        s.sponsor_code,
                        a.id as assessment_id,
                        a.assessment_date,
                        a.next_review_date,
                        a.status as assessment_status,
                        a.conducted_by_name,
                        a.conducted_by_email,
                        a.updated_by_name,
                        a.updated_by_email,
                        a.created_at as assessment_created_at,
                        a.updated_at as assessment_updated_at
                    FROM "{self.schema_name}".assessment_notifications n
                    JOIN "{self.schema_name}".riskassessment_site_study s ON n.study_id = s.id
                    LEFT JOIN "{self.schema_name}".assessments a ON s.id = a.study_id
                    WHERE n.target_user_type = 'SD' AND s.status != 'Inactive'
                    ORDER BY n.action_date DESC
                    LIMIT 50
                """
            else:  # PI
                # PI gets notifications about SD actions and SD-created assessments
                query = f"""
                    SELECT 
                        n.id,
                        n.assessment_id,
                        n.action,
                        n.action_by_name,
                        n.action_by_email,
                        n.reason,
                        n.comments,
                        n.action_date,
                        n.read_status,
                        s.id as study_id,
                        s.site,
                        s.sponsor,
                        s.protocol,
                        s.studytype as study_type,
                        s.studytypetext as study_type_text,
                        s.description,
                        s.status as study_status,
                        s.phase,
                        a.monitoring_schedule,
                        s.siteid,
                        s.studyid,
                        s.active,
                        s.principal_investigator,
                        s.principal_investigator_email,
                        s.site_director,
                        s.site_director_email,
                        s.sponsor_code,
                        a.id as assessment_id,
                        a.assessment_date,
                        a.next_review_date,
                        a.status as assessment_status,
                        a.conducted_by_name,
                        a.conducted_by_email,
                        a.updated_by_name,
                        a.updated_by_email,
                        a.created_at as assessment_created_at,
                        a.updated_at as assessment_updated_at
                    FROM "{self.schema_name}".assessment_notifications n
                    JOIN "{self.schema_name}".riskassessment_site_study s ON n.study_id = s.id
                    LEFT JOIN "{self.schema_name}".assessments a ON s.id = a.study_id
                    WHERE n.target_user_type = 'PI' AND s.status != 'Inactive'
                    ORDER BY n.action_date DESC
                    LIMIT 50
                """
            
            notifications_data = db.execute_query(query)
            
            # Convert to AssessmentNotification objects
            notifications = []
            unread_count = 0
            
            for row in notifications_data:
                notification_dict = dict(row)
                
                # Convert datetime objects to strings
                if notification_dict.get('action_date'):
                    notification_dict['action_date'] = notification_dict['action_date'].isoformat()
                if notification_dict.get('assessment_date'):
                    notification_dict['assessment_date'] = notification_dict['assessment_date'].isoformat()
                if notification_dict.get('next_review_date'):
                    notification_dict['next_review_date'] = notification_dict['next_review_date'].isoformat()
                if notification_dict.get('assessment_created_at'):
                    notification_dict['assessment_created_at'] = notification_dict['assessment_created_at'].isoformat()
                if notification_dict.get('assessment_updated_at'):
                    notification_dict['assessment_updated_at'] = notification_dict['assessment_updated_at'].isoformat()
                
                # Create StudyInfo object with all fields
                study_info = StudyInfo(
                    site=notification_dict.get('site', ''),
                    sponsor=notification_dict.get('sponsor', ''),
                    protocol=notification_dict.get('protocol', ''),
                    study_description=notification_dict.get('description', ''),
                    study_type=notification_dict.get('study_type'),
                    study_type_text=notification_dict.get('study_type_text'),
                    study_status=notification_dict.get('study_status'),
                    phase=notification_dict.get('phase'),
                    monitoring_schedule=notification_dict.get('monitoring_schedule'),
                    siteid=notification_dict.get('siteid'),
                    studyid=notification_dict.get('studyid'),
                    active=notification_dict.get('active'),
                    principal_investigator=notification_dict.get('principal_investigator'),
                    principal_investigator_email=notification_dict.get('principal_investigator_email'),
                    site_director=notification_dict.get('site_director'),
                    site_director_email=notification_dict.get('site_director_email'),
                    sponsor_code=notification_dict.get('sponsor_code'),
                    created_at=None  # This field doesn't exist in the studies table
                )
                
                # Create AssessmentInfo object with all fields
                assessment_info = AssessmentInfo(
                    assessment_id=notification_dict.get('assessment_id'),
                    assessment_date=notification_dict.get('assessment_date'),
                    next_review_date=notification_dict.get('next_review_date'),
                    status=notification_dict.get('assessment_status'),
                    conducted_by_name=notification_dict.get('conducted_by_name'),
                    conducted_by_email=notification_dict.get('conducted_by_email'),
                    updated_by_name=notification_dict.get('updated_by_name'),
                    updated_by_email=notification_dict.get('updated_by_email'),
                    created_at=notification_dict.get('assessment_created_at'),
                    updated_at=notification_dict.get('assessment_updated_at')
                )
                
                # Create AssessmentNotification object
                notification = AssessmentNotification(
                    id=notification_dict['id'],
                    assessment_id=notification_dict['assessment_id'],
                    action=notification_dict['action'],
                    action_by_name=notification_dict['action_by_name'],
                    action_by_email=notification_dict['action_by_email'],
                    reason=notification_dict['reason'],
                    comments=notification_dict['comments'],
                    action_date=notification_dict['action_date'],
                    read=notification_dict.get('read_status', False),
                    study_info=study_info,
                    assessment_info=assessment_info,
                    pi_name=notification_dict.get('principal_investigator'),
                    pi_email=notification_dict.get('principal_investigator_email'),
                    sd_name=notification_dict.get('site_director'),
                    sd_email=notification_dict.get('site_director_email')
                )
                
                notifications.append(notification)
                
                if not notification.read:
                    unread_count += 1
            
            return NotificationResponse(
                notifications=notifications,
                unread_count=unread_count
            )
            
        except Exception as e:
            logger.error(f"Error getting notifications: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")
    
    def mark_as_read(self, notification_id: int) -> Dict[str, Any]:
        """
        Mark a specific notification as read
        """
        try:
            update_query = f"""
                UPDATE "{self.schema_name}".assessment_notifications
                SET read_status = true, updated_at = %s
                WHERE id = %s
            """
            
            current_time = datetime.now()
            result = db.execute_query(update_query, [current_time, notification_id])
            
            if result == 0:
                raise HTTPException(status_code=404, detail="Notification not found")
            
            logger.info(f"Marked notification {notification_id} as read")
            
            return {
                "success": True,
                "message": "Notification marked as read"
            }
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")
    
    def mark_all_as_read(self, user_type: str) -> Dict[str, Any]:
        """
        Mark all notifications as read for a specific user type
        """
        try:
            update_query = f"""
                UPDATE "{self.schema_name}".assessment_notifications
                SET read_status = true, updated_at = %s
                WHERE target_user_type = %s AND read_status = false
            """
            
            current_time = datetime.now()
            result = db.execute_query(update_query, [current_time, user_type.upper()])
            
            logger.info(f"Marked {result} notifications as read for user type {user_type}")
            
            return {
                "success": True,
                "message": f"Marked {result} notifications as read",
                "updated_count": result
            }
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to mark all notifications as read: {str(e)}")

    def get_unread_count(self, user_type: str, user_email: str) -> Dict[str, Any]:
        """
        Get the count of unread notifications for a specific user type and email
        This is more efficient than getting all notifications just for the count
        """
        try:
            logger.info(f"Getting unread count for user type: {user_type}, email: {user_email}")
            
            # Simple count query for unread notifications
            query = f"""
                SELECT COUNT(*) as unread_count
                FROM "{self.schema_name}".assessment_notifications
                WHERE target_user_type = %s AND read_status = false
            """
            
            result = db.execute_query(query, [user_type.upper()])
            
            if result:
                unread_count = result[0]['unread_count']
                logger.info(f"Found {unread_count} unread notifications for user type {user_type}")
                
                return {
                    "unread_count": unread_count,
                    "user_type": user_type.upper(),
                    "user_email": user_email
                }
            else:
                logger.warning(f"No result returned for unread count query")
                return {
                    "unread_count": 0,
                    "user_type": user_type.upper(),
                    "user_email": user_email
                }
                
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get unread count: {str(e)}")

    def create_assessment_submission_notification(self, assessment_id: int, study_id: int, 
                                                submitter_name: str, submitter_email: str,
                                                submitter_type: str) -> Dict[str, Any]:
        """
        Create notification when assessment is submitted (target user type based on submitter)
        - If PI submits: target is SD
        - If SD submits: target is PI
        """
        # Determine target user type based on submitter type
        print("line 242")
        print(f"Submitter type: {submitter_type}")
        if submitter_type.upper() == 'PI':
            target_user_type = 'SD'
            action_name = 'Initial Save'
            reason = 'Assessment saved by Principal Investigator'
            comments = 'Assessment data saved successfully by PI'
        elif submitter_type.upper() == 'SD':
            target_user_type = 'PI'
            action_name = 'SD Created'
            reason = 'Assessment created by Study Director'
            comments = 'Study Director has created an assessment that requires your review'
        else:
            # Default to SD if submitter type is unknown
            target_user_type = 'SD'
            action_name = 'Initial Save'
            reason = 'Assessment saved'
            comments = 'Assessment data saved successfully'
        
        notification_data = {
            "assessment_id": assessment_id,
            "action": action_name,
            "action_by_name": submitter_name,
            "action_by_email": submitter_email,
            "reason": reason,
            "comments": comments,
            "target_user_type": target_user_type,
            "study_id": study_id
        }
        
        logger.info(f"Creating {target_user_type} notification for {submitter_type} submission")
        return self.create_notification(notification_data)
    
    def create_assessment_approval_notification(self, assessment_id: int, study_id: int,
                                              sd_name: str, sd_email: str, 
                                              pi_name: str, pi_email: str,
                                              action: str, reason: str, comments: str) -> Dict[str, Any]:
        """
        Create notification when SD approves/rejects an assessment (for PI to see)
        """
        notification_data = {
            "assessment_id": assessment_id,
            "action": action,
            "action_by_name": sd_name,
            "action_by_email": sd_email,
            "reason": reason,
            "comments": comments,
            "target_user_type": "PI",
            "study_id": study_id
        }
        
        return self.create_notification(notification_data)
    
    def create_sd_assessment_notification(self, assessment_id: int, study_id: int,
                                        sd_name: str, sd_email: str,
                                        pi_name: str, pi_email: str) -> Dict[str, Any]:
        """
        Create notification when SD creates an assessment (for PI to review)
        """
        notification_data = {
            "assessment_id": assessment_id,
            "action": "SD Created",
            "action_by_name": sd_name,
            "action_by_email": sd_email,
            "reason": "Assessment created by Study Director",
            "comments": "Study Director has created an assessment that requires your review",
            "target_user_type": "PI",
            "study_id": study_id
        }
        
        return self.create_notification(notification_data)

# Global notification service instance
notification_service = NotificationService() 