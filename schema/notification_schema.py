from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class StudyInfo(BaseModel):
    site: str
    sponsor: str
    protocol: str
    study_description: str
    study_type: Optional[str] = None
    study_type_text: Optional[str] = None
    study_status: Optional[str] = None
    phase: Optional[str] = None
    monitoring_schedule: Optional[str] = None
    siteid: Optional[int] = None
    studyid: Optional[str] = None
    active: Optional[bool] = None
    principal_investigator: Optional[str] = None
    principal_investigator_email: Optional[str] = None
    site_director: Optional[str] = None
    site_director_email: Optional[str] = None
    sponsor_code: Optional[str] = None
    created_at: Optional[str] = None

class AssessmentInfo(BaseModel):
    assessment_id: Optional[int] = None
    assessment_date: Optional[str] = None
    next_review_date: Optional[str] = None
    status: Optional[str] = None
    conducted_by_name: Optional[str] = None
    conducted_by_email: Optional[str] = None
    updated_by_name: Optional[str] = None
    updated_by_email: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class AssessmentNotification(BaseModel):
    id: int
    assessment_id: int
    action: str
    action_by_name: str
    action_by_email: str
    reason: str
    comments: str
    action_date: str
    read: Optional[bool] = False
    study_info: Optional[StudyInfo] = None
    assessment_info: Optional[AssessmentInfo] = None
    pi_name: Optional[str] = None
    pi_email: Optional[str] = None
    sd_name: Optional[str] = None
    sd_email: Optional[str] = None

class NotificationResponse(BaseModel):
    notifications: List[AssessmentNotification]
    unread_count: int

class MarkAsReadRequest(BaseModel):
    notification_id: int

class MarkAllAsReadRequest(BaseModel):
    user_type: str  # 'PI' or 'SD'

class CreateNotificationRequest(BaseModel):
    assessment_id: int
    action: str
    action_by_name: str
    action_by_email: str
    reason: str
    comments: str
    target_user_type: str  # 'PI' or 'SD' - who should receive this notification
    study_id: int 