from fastapi import APIRouter, Depends, Body, HTTPException
from typing import Dict, Any
from core.auth_middleware import require_auth
from services.assessment_service import assessment_service
from services.notification_service import notification_service
from schema.assessment_schema import MetadataResponse, AssessmentCreate, AssessmentResponse, AssessmentApprovalRequest, AssessmentApprovalResponse
import logging
from database.connection import db

logger = logging.getLogger(__name__)

router = APIRouter()

# Test endpoint to verify router is working
@router.get("/test")
async def test_endpoint():
    """
    Test endpoint to verify the assessment router is working
    """
    return {"message": "Assessment router is working!", "status": "success"}

@router.get("/metadata", response_model=MetadataResponse)
async def get_assessment_metadata(
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get assessment sections and risk factors metadata for the UI
    """
    return assessment_service.get_metadata()

@router.post("/saveRisksByStudyId", response_model=Dict[str, Any])
async def save_assessment(
    assessment_data: AssessmentCreate = Body(...),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Save assessment data - creates or updates assessment record and risk scores
    """
    try:
        logger.info("=== ASSESSMENT SAVE REQUEST START ===")
        logger.info(f"Current user: {current_user}")
        logger.info(f"Received assessment data: {assessment_data}")
        
        # Convert Pydantic model to dict, handling nested models properly
        assessment_dict = assessment_data.dict()
        logger.info(f"Converted to dict: {assessment_dict}")
        
        logger.info("Calling assessment service...")
        result = assessment_service.save_assessment(assessment_dict, current_user)
        logger.info(f"Service returned: {result}")
        logger.info("=== ASSESSMENT SAVE REQUEST END ===")
        
        return result
        
    except Exception as e:
        logger.error(f"=== ASSESSMENT SAVE ERROR ===")
        logger.error(f"Error in save_assessment endpoint: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error(f"=== END ERROR ===")
        raise HTTPException(status_code=500, detail=f"Failed to save assessment: {str(e)}")

@router.post("/saveDraft", response_model=Dict[str, Any])
async def save_assessment_draft(
    assessment_data: AssessmentCreate = Body(...),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Save assessment data as draft - allows partial data with minimal validation
    """
    try:
        logger.info("=== ASSESSMENT DRAFT SAVE REQUEST START ===")
        logger.info(f"Current user: {current_user}")
        logger.info(f"Received assessment data: {assessment_data}")
        
        # Convert Pydantic model to dict, handling nested models properly
        assessment_dict = assessment_data.dict()
        logger.info(f"Converted to dict: {assessment_dict}")
        
        logger.info("Calling assessment service save_assessment_draft...")
        result = assessment_service.save_assessment_draft(assessment_dict, current_user)
        logger.info(f"Service returned: {result}")
        logger.info("=== ASSESSMENT DRAFT SAVE REQUEST END ===")
        
        return result
        
    except Exception as e:
        logger.error(f"=== ASSESSMENT DRAFT SAVE ERROR ===")
        logger.error(f"Error in save_assessment_draft endpoint: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error(f"=== END ERROR ===")
        raise HTTPException(status_code=500, detail=f"Failed to save assessment draft: {str(e)}")

@router.get("/{assessment_id}/complete", response_model=Dict[str, Any])
async def get_complete_assessment(
    assessment_id: int,
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get complete assessment data including risk scores, mitigation plans, dashboard, and comments
    """
    try:
        logger.info(f"Getting complete assessment data for ID: {assessment_id}")
        result = assessment_service.get_complete_assessment(assessment_id)
        logger.info(f"Complete assessment data retrieved successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error getting complete assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get complete assessment: {str(e)}")

@router.get("/by-study/{study_id}/complete", response_model=Dict[str, Any])
async def get_complete_assessment_by_study(
    study_id: int,
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get complete assessment data by study ID including risk scores, mitigation plans, dashboard, and comments
    """
    try:
        logger.info(f"Getting complete assessment data for study ID: {study_id}")
        result = assessment_service.get_complete_assessment_by_study_id(study_id)
        logger.info(f"Complete assessment data by study retrieved successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error getting complete assessment by study: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get complete assessment by study: {str(e)}")

@router.get("/assessed-studies", response_model=Dict[str, Any])
async def get_assessed_studies(
    user_type: str = None,
    current_user: Dict[str, Any] = Depends(require_auth())
):
    print("104")
    print(user_type)
    """
    Get all studies that have assessments with complete assessment data and approval info
    Optional user_type parameter to filter by PI or SD
    """
    try:
        logger.info(f"=== ASSESSED STUDIES ENDPOINT START ===")
        logger.info(f"Current user data: {current_user}")
        logger.info(f"User email: {current_user.get('email')}")
        logger.info(f"User name: {current_user.get('name')}")
        logger.info(f"User type parameter: {user_type}")
        
        # Check if the user has an email
        user_email = current_user.get('email')
        if not user_email:
            logger.warning("No email found in user data, using mock email for testing")
            current_user['email'] = "test@example.com"
        user_email = user_email.lower()  # Convert to lowercase for consistent comparison
        
        result = assessment_service.get_assessed_studies(current_user, user_type)
        logger.info(f"Assessed studies retrieved successfully")
        logger.info(f"=== ASSESSED STUDIES ENDPOINT END ===")
        return result
        
    except Exception as e:
        logger.error(f"=== ASSESSED STUDIES ENDPOINT ERROR ===")
        logger.error(f"Error getting assessed studies: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error(f"=== END ASSESSED STUDIES ENDPOINT ERROR ===")
        raise HTTPException(status_code=500, detail=f"Failed to get assessed studies: {str(e)}") 

@router.get("/dashboard-stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    user_type: str,
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get dashboard statistics for PI or Site Director
    user_type: 'PI' for Principal Investigator or 'SD' for Site Director
    """
    try:
        logger.info(f"Getting dashboard stats for user: {current_user.get('email')}, type: {user_type}")
        
        user_email = current_user.get('email')
        if not user_email:
            raise HTTPException(status_code=400, detail="Email not found in token")
        user_email = user_email.lower()  # Convert to lowercase for consistent comparison
        
        if user_type.upper() not in ['PI', 'SD']:
            raise HTTPException(status_code=400, detail="user_type must be 'PI' or 'SD'")
        
        result = assessment_service.get_dashboard_stats(user_email, user_type.upper())
        logger.info(f"Dashboard stats retrieved successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}") 

@router.post("/{assessment_id}/approve", response_model=AssessmentApprovalResponse)
async def approve_assessment(assessment_id: int, request: AssessmentApprovalRequest):
    """
    Approve an assessment by Site Director (SD)
    """
    try:
        # Check if assessment exists and can be approved
        assessment_query = """
            SELECT id, study_id, status 
            FROM "Risk Assessment".assessments 
            WHERE id = %s
        """
        assessment_result = db.execute_query(assessment_query, [assessment_id])
        
        if not assessment_result:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        assessment = assessment_result[0]
        if assessment['status'] not in ['Pending Review', 'In Progress']:
            raise HTTPException(
                status_code=400, 
                detail=f"Assessment cannot be approved. Current status: {assessment['status']}"
            )
        
        # Update assessment status
        update_query = """
            UPDATE "Risk Assessment".assessments 
            SET 
                status = 'Approved',
                updated_by_name = %s,
                updated_by_email = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        db.execute_query(update_query, [request.action_by_name, request.action_by_email, assessment_id])
        
        # Get the updated assessment data
        select_query = """
            SELECT id, study_id, status, updated_by_name, updated_by_email, updated_at
            FROM "Risk Assessment".assessments 
            WHERE id = %s
        """
        updated_assessment_result = db.execute_query(select_query, [assessment_id])
        updated_assessment = updated_assessment_result[0]
        
        # Insert approval record
        approval_query = """
            INSERT INTO "Risk Assessment".assessment_approvals (
                assessment_id, 
                action, 
                action_by_name, 
                action_by_email, 
                reason, 
                comments, 
                action_date
            ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """
        db.execute_query(approval_query, [
            assessment_id, 
            'Approved', 
            request.action_by_name, 
            request.action_by_email, 
            request.reason, 
            request.comments
        ])
        
        # Get the inserted approval record
        approval_select_query = """
            SELECT id, assessment_id, action, action_by_name, 
                   action_by_email, reason, comments, action_date
            FROM "Risk Assessment".assessment_approvals
            WHERE assessment_id = %s AND action = 'Approved'
            ORDER BY action_date DESC
            LIMIT 1
        """
        approval_result = db.execute_query(approval_select_query, [assessment_id])
        approval_record = approval_result[0]
        
        # Prepare response
        assessment_data = {
            "id": updated_assessment['id'],
            "study_id": updated_assessment['study_id'],
            "status": updated_assessment['status'],
            "updated_by_name": updated_assessment['updated_by_name'],
            "updated_by_email": updated_assessment['updated_by_email'],
            "updated_at": updated_assessment['updated_at'].isoformat()
        }
        
        approval_data = {
            "id": approval_record['id'],
            "assessment_id": approval_record['assessment_id'],
            "action": approval_record['action'],
            "action_by_name": approval_record['action_by_name'],
            "action_by_email": approval_record['action_by_email'],
            "reason": approval_record['reason'],
            "comments": approval_record['comments'],
            "action_date": approval_record['action_date'].isoformat()
        }
        
        # Create notification for PI when SD approves assessment
        try:
            # Get PI information from the study
            pi_query = """
                SELECT principal_investigator, principal_investigator_email 
                FROM "Risk Assessment".riskassessment_site_study
                WHERE id = %s AND status != 'Inactive'
            """
            pi_result = db.execute_query(pi_query, [assessment['study_id']])
            
            if pi_result:
                pi_name = pi_result[0]['principal_investigator'] or "Unknown PI"
                pi_email = pi_result[0]['principal_investigator_email'] or "unknown@email.com"
                
                notification_result = notification_service.create_assessment_approval_notification(
                    assessment_id=assessment_id,
                    study_id=assessment['study_id'],
                    sd_name=request.action_by_name,
                    sd_email=request.action_by_email,
                    pi_name=pi_name,
                    pi_email=pi_email,
                    action="Approved",
                    reason=request.reason,
                    comments=request.comments or "Assessment has been reviewed and approved by Study Director"
                )
                logging.info(f"Created approval notification: {notification_result}")
            else:
                logging.warning(f"PI information not found for study {assessment['study_id']}")
        except Exception as notification_error:
            logging.warning(f"Failed to create approval notification: {notification_error}")
            # Don't fail the approval if notification fails
        
        return AssessmentApprovalResponse(
            success=True,
            message="Assessment approved successfully",
            assessment=assessment_data,
            approval_data=approval_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error approving assessment {assessment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{assessment_id}/reject", response_model=AssessmentApprovalResponse)
async def reject_assessment(assessment_id: int, request: AssessmentApprovalRequest):
    """
    Reject an assessment by Site Director (SD)
    """
    try:
        # Check if assessment exists and can be rejected
        assessment_query = """
            SELECT id, study_id, status 
            FROM "Risk Assessment".assessments 
            WHERE id = %s
        """
        assessment_result = db.execute_query(assessment_query, [assessment_id])
        
        if not assessment_result:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        assessment = assessment_result[0]
        if assessment['status'] not in ['Pending Review', 'In Progress']:
            raise HTTPException(
                status_code=400, 
                detail=f"Assessment cannot be rejected. Current status: {assessment['status']}"
            )
        
        # Validate that reason is provided for rejection
        if not request.reason or not request.reason.strip():
            raise HTTPException(
                status_code=400, 
                detail="Reason is required for rejection"
            )
        
        # Update assessment status
        update_query = """
            UPDATE "Risk Assessment".assessments 
            SET 
                status = 'Rejected',
                updated_by_name = %s,
                updated_by_email = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        db.execute_query(update_query, [request.action_by_name, request.action_by_email, assessment_id])
        
        # Get the updated assessment data
        select_query = """
            SELECT id, study_id, status, updated_by_name, updated_by_email, updated_at
            FROM "Risk Assessment".assessments 
            WHERE id = %s
        """
        updated_assessment_result = db.execute_query(select_query, [assessment_id])
        updated_assessment = updated_assessment_result[0]
        
        # Insert approval record
        approval_query = """
            INSERT INTO "Risk Assessment".assessment_approvals (
                assessment_id, 
                action, 
                action_by_name, 
                action_by_email, 
                reason, 
                comments, 
                action_date
            ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """
        db.execute_query(approval_query, [
            assessment_id, 
            'Rejected', 
            request.action_by_name, 
            request.action_by_email, 
            request.reason, 
            request.comments
        ])
        
        # Get the inserted approval record
        approval_select_query = """
            SELECT id, assessment_id, action, action_by_name, 
                   action_by_email, reason, comments, action_date
            FROM "Risk Assessment".assessment_approvals
            WHERE assessment_id = %s AND action = 'Rejected'
            ORDER BY action_date DESC
            LIMIT 1
        """
        approval_result = db.execute_query(approval_select_query, [assessment_id])
        approval_record = approval_result[0]
        
        # Prepare response
        assessment_data = {
            "id": updated_assessment['id'],
            "study_id": updated_assessment['study_id'],
            "status": updated_assessment['status'],
            "updated_by_name": updated_assessment['updated_by_name'],
            "updated_by_email": updated_assessment['updated_by_email'],
            "updated_at": updated_assessment['updated_at'].isoformat()
        }
        
        approval_data = {
            "id": approval_record['id'],
            "assessment_id": approval_record['assessment_id'],
            "action": approval_record['action'],
            "action_by_name": approval_record['action_by_name'],
            "action_by_email": approval_record['action_by_email'],
            "reason": approval_record['reason'],
            "comments": approval_record['comments'],
            "action_date": approval_record['action_date'].isoformat()
        }
        
        # Create notification for PI when SD rejects assessment
        try:
            # Get PI information from the study
            pi_query = """
                SELECT principal_investigator, principal_investigator_email 
                FROM "Risk Assessment".riskassessment_site_study
                WHERE id = %s AND status != 'Inactive'
            """
            pi_result = db.execute_query(pi_query, [assessment['study_id']])
            
            if pi_result:
                pi_name = pi_result[0]['principal_investigator'] or "Unknown PI"
                pi_email = pi_result[0]['principal_investigator_email'] or "unknown@email.com"
                
                notification_result = notification_service.create_assessment_approval_notification(
                    assessment_id=assessment_id,
                    study_id=assessment['study_id'],
                    sd_name=request.action_by_name,
                    sd_email=request.action_by_email,
                    pi_name=pi_name,
                    pi_email=pi_email,
                    action="Rejected",
                    reason=request.reason,
                    comments=request.comments or "Assessment has been reviewed and rejected by Study Director"
                )
                logging.info(f"Created rejection notification: {notification_result}")
            else:
                logging.warning(f"PI information not found for study {assessment['study_id']}")
        except Exception as notification_error:
            logging.warning(f"Failed to create rejection notification: {notification_error}")
            # Don't fail the rejection if notification fails
        
        return AssessmentApprovalResponse(
            success=True,
            message="Assessment rejected successfully",
            assessment=assessment_data,
            approval_data=approval_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error rejecting assessment {assessment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")