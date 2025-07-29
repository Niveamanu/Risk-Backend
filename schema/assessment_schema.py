from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date

class AssessmentSection(BaseModel):
    id: int
    section_key: str
    section_title: str
    created_at: Optional[str]

class RiskFactor(BaseModel):
    id: int
    assessment_section_id: int
    risk_factor_text: str
    risk_factor_code: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: Optional[str]

class RiskScoreData(BaseModel):
    risk_factor_id: int
    severity: int
    likelihood: int
    risk_score: int
    risk_level: str
    mitigation_actions: Optional[str]
    custom_notes: Optional[str]

class RiskMitigationPlan(BaseModel):
    risk_item: str
    responsible_person: Optional[str]
    mitigation_strategy: Optional[str]
    target_date: Optional[str]  # Date as string "YYYY-MM-DD"
    status: Optional[str] = "Pending"
    priority_level: Optional[str] = "High"

class RiskDashboardData(BaseModel):
    total_risks: Optional[int] = 0
    high_risk_count: Optional[int] = 0
    medium_risk_count: Optional[int] = 0
    low_risk_count: Optional[int] = 0
    total_score: Optional[int] = 0
    overall_risk_level: Optional[str]
    risk_level_criteria: Optional[str]

class SummaryComment(BaseModel):
    comment_type: Optional[str]  # 'General', 'Mitigation', 'Dashboard', 'Overall'
    comment_text: Optional[str]

class SectionComment(BaseModel):
    section_key: str
    section_title: str
    comment_text: str

class AssessmentCreate(BaseModel):
    study_id: int
    assessment_date: str
    next_review_date: Optional[str]
    monitoring_schedule: Optional[str]
    overall_risk_score: Optional[int]
    overall_risk_level: Optional[str]
    comments: Optional[str]
    risk_scores: List[RiskScoreData]
    # New fields for Summary page
    risk_mitigation_plans: Optional[List[RiskMitigationPlan]] = []
    risk_dashboard: Optional[RiskDashboardData] = None
    summary_comments: Optional[List[SummaryComment]] = []
    section_comments: Optional[List[SectionComment]] = []

class AssessmentResponse(BaseModel):
    id: int
    study_id: int
    conducted_by_name: Optional[str]
    conducted_by_email: Optional[str]
    assessment_date: str
    next_review_date: Optional[str]
    monitoring_schedule: Optional[str]
    status: str
    overall_risk_score: Optional[int]
    overall_risk_level: Optional[str]
    comments: Optional[str]
    updated_by_name: Optional[str]
    updated_by_email: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

class MetadataResponse(BaseModel):
    assessment_sections: List[AssessmentSection]
    risk_factors: List[RiskFactor] 


class AssessmentApprovalRequest(BaseModel):
    study_id: int
    assessment_id: int
    action: str  # "Approved" or "Rejected"
    reason: str
    comments: Optional[str] = None
    action_by_name: str
    action_by_email: str

class AssessmentApprovalResponse(BaseModel):
    success: bool
    message: str
    assessment: dict
    approval_data: dict