#!/usr/bin/env python3
"""
Audit Router for assessment audit trail endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, Any, Optional
from core.auth_middleware import require_auth
from services.audit_service import audit_service
from database.connection import db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/audit-trail/{assessment_id}")
async def get_audit_trail(
    assessment_id: int,
    field_name: Optional[str] = Query(None, description="Filter by field name (e.g., 'severity', 'risk_score')"),
    risk_factor_id: Optional[int] = Query(None, description="Filter by risk factor ID"),
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get audit trail for a specific assessment
    """
    try:
        logger.info(f"Getting audit trail for assessment {assessment_id}")
        
        result = audit_service.get_audit_trail_for_assessment(
            assessment_id=assessment_id,
            field_name=field_name,
            risk_factor_id=risk_factor_id,
            limit=limit
        )
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "audit_trail": result,
            "total_records": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting audit trail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit trail: {str(e)}")

@router.get("/audit-trail/{assessment_id}/severity-changes")
async def get_severity_changes(
    assessment_id: int,
    risk_factor_id: Optional[int] = Query(None, description="Filter by risk factor ID"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get all severity changes for an assessment
    """
    try:
        logger.info(f"Getting severity changes for assessment {assessment_id}")
        
        result = audit_service.get_severity_changes(
            assessment_id=assessment_id,
            risk_factor_id=risk_factor_id
        )
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "severity_changes": result,
            "total_changes": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting severity changes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get severity changes: {str(e)}")

@router.get("/audit-trail/{assessment_id}/risk-score-changes")
async def get_risk_score_changes(
    assessment_id: int,
    risk_factor_id: Optional[int] = Query(None, description="Filter by risk factor ID"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get all risk score changes for an assessment
    """
    try:
        logger.info(f"Getting risk score changes for assessment {assessment_id}")
        
        result = audit_service.get_risk_score_changes(
            assessment_id=assessment_id,
            risk_factor_id=risk_factor_id
        )
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "risk_score_changes": result,
            "total_changes": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting risk score changes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk score changes: {str(e)}")

@router.get("/audit-trail/{assessment_id}/risk-level-changes")
async def get_risk_level_changes(
    assessment_id: int,
    risk_factor_id: Optional[int] = Query(None, description="Filter by risk factor ID"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get all risk level changes for an assessment
    """
    try:
        logger.info(f"Getting risk level changes for assessment {assessment_id}")
        
        result = audit_service.get_risk_level_changes(
            assessment_id=assessment_id,
            risk_factor_id=risk_factor_id
        )
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "risk_level_changes": result,
            "total_changes": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting risk level changes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk level changes: {str(e)}")

@router.get("/audit-trail/{assessment_id}/user-changes")
async def get_changes_by_user(
    assessment_id: int,
    user_email: str = Query(..., description="Email of the user to filter by"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get all changes made by a specific user for an assessment
    """
    try:
        logger.info(f"Getting changes by user {user_email} for assessment {assessment_id}")
        
        result = audit_service.get_changes_by_user(
            assessment_id=assessment_id,
            user_email=user_email
        )
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "user_email": user_email,
            "user_changes": result,
            "total_changes": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting user changes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user changes: {str(e)}")

@router.get("/audit-trail/{assessment_id}/summary")
async def get_audit_summary(
    assessment_id: int,
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get a summary of audit trail for an assessment
    """
    try:
        logger.info(f"Getting audit summary for assessment {assessment_id}")
        
        result = audit_service.get_audit_summary(assessment_id=assessment_id)
        
        return {
            "success": True,
            "summary": result
        }
        
    except Exception as e:
        logger.error(f"Error getting audit summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit summary: {str(e)}")

@router.get("/audit-trail/{assessment_id}/risk-factor/{risk_factor_id}")
async def get_risk_factor_audit_trail(
    assessment_id: int,
    risk_factor_id: int,
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get audit trail for a specific risk factor within an assessment
    """
    try:
        logger.info(f"Getting audit trail for risk factor {risk_factor_id} in assessment {assessment_id}")
        
        result = audit_service.get_audit_trail_for_risk_factor(
            assessment_id=assessment_id,
            risk_factor_id=risk_factor_id
        )
        
        return {
            "success": True,
            "assessment_id": assessment_id,
            "risk_factor_id": risk_factor_id,
            "audit_trail": result,
            "total_records": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting risk factor audit trail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk factor audit trail: {str(e)}")

@router.get("/assessment-audit/{study_id}")
async def get_assessment_audit_for_ui(
    study_id: int,
    field_name: Optional[str] = Query(None, description="Filter by field name (e.g., 'Severity', 'Risk Score')"),
    risk_factor_id: Optional[int] = Query(None, description="Filter by risk factor ID"),
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get assessment audit trail for UI display - returns data in UI-compatible format
    This endpoint is designed to work with the assessment audit grid in the frontend
    """
    try:
        logger.info(f"Getting assessment audit trail for study {study_id} for UI display")
        
        # First, get the assessment ID for this study
        assessment_query = """
            SELECT id FROM "Risk Assessment".assessments
            WHERE study_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        assessment_result = db.execute_query(assessment_query, [study_id])
        
        if not assessment_result:
            return {
                "success": True,
                "study_id": study_id,
                "assessment_id": None,
                "audit_data": [],
                "total_records": 0,
                "message": "No assessment found for this study"
            }
        
        assessment_id = assessment_result[0]['id']
        
        # Get audit trail data
        result = audit_service.get_audit_trail_for_assessment(
            assessment_id=assessment_id,
            field_name=field_name,
            risk_factor_id=risk_factor_id,
            limit=limit
        )
        
        # Transform the data to match the UI format exactly
        ui_audit_data = []
        for entry in result:
            ui_audit_data.append({
                "timestamp": entry.get("timestamp", ""),
                "riskFactor": entry.get("riskFactor", ""),
                "field": entry.get("field", ""),
                "oldValue": entry.get("oldValue", ""),
                "newValue": entry.get("newValue", ""),
                "changedBy": entry.get("changedBy", "")
            })
        
        return {
            "success": True,
            "study_id": study_id,
            "assessment_id": assessment_id,
            "audit_data": ui_audit_data,
            "total_records": len(ui_audit_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting assessment audit trail for UI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get assessment audit trail: {str(e)}")

@router.get("/assessment-timeline/{study_id}")
async def get_assessment_timeline_for_ui(
    study_id: int,
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get assessment timeline for UI display - returns data in UI-compatible format
    This endpoint is designed to work with the assessment timeline grid in the frontend
    """
    try:
        logger.info(f"Getting assessment timeline for study {study_id} for UI display")
        
        # Get timeline data with summary comments from assessment_summary_comments table
        timeline_query = """
            SELECT 
                at.id,
                at.study_id,
                at.assessment_id,
                at.schedule_type as schedule,
                at.assessed_date,
                at.assessed_by_name as assessed_by,
                at.risk_score,
                at.risk_level,
                    at.notes ,
                at.created_at
            FROM "Risk Assessment".assessment_timeline at
            WHERE at.study_id = %s
            ORDER BY at.created_at DESC
            LIMIT %s
        """
        timeline_result = db.execute_query(timeline_query, [study_id, limit])
        
        # Transform the data to match the UI format exactly
        ui_timeline_data = []
        for entry in timeline_result:
            ui_timeline_data.append({
                "id": entry.get("id", 0),
                "schedule": entry.get("schedule", ""),
                "assessedDate": entry.get("assessed_date").strftime('%Y-%m-%d') if entry.get("assessed_date") else "",
                "assessedBy": entry.get("assessed_by", ""),
                "riskScore": entry.get("risk_score", 0),
                "riskLevel": entry.get("risk_level", ""),
                "notes": entry.get("notes", ""),
                "createdAt": entry.get("created_at").strftime('%Y-%m-%d %H:%M:%S') if entry.get("created_at") else ""
            })
        
        return {
            "success": True,
            "study_id": study_id,
            "timeline_data": ui_timeline_data,
            "total_records": len(ui_timeline_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting assessment timeline for UI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get assessment timeline: {str(e)}")

# Test endpoint
@router.get("/audit-trail/test")
async def test_audit_endpoint():
    """
    Test endpoint to verify the audit router is working
    """
    return {"message": "Audit router is working!", "status": "success"} 