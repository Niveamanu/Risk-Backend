from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from typing import Dict, Any, List, Optional
from core.auth_middleware import require_auth
from services.studies_service import studies_service
from schema.studies_schema import StudyResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[StudyResponse])
async def get_studies(
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get all studies
    """
    try:
        return studies_service.get_studies()
    except Exception as e:
        logger.error(f"Error getting studies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get studies: {str(e)}")

@router.get("/assessments", response_model=List[Dict[str, Any]])
async def get_assessments_with_contacts(
    current_user: Dict[str, Any] = Depends(require_auth()),
    user_type: Optional[str] = Query(None, description="Type of user: 'PI' or 'Site Director'")
):
    """
    Get assessments with contact information based on user type.
    If user_type is 'PI', search in principal_investigator_email.
    If user_type is 'Site Director', search in site_director_email.
    If no user_type provided, return all assessments.
    """
    try:
        logger.info(f"Getting assessments with user_type: {user_type}")
        return studies_service.get_assessments_with_contacts(user_type, current_user)
    except Exception as e:
        logger.error(f"Error getting assessments with contacts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get assessments: {str(e)}")

@router.get("/dropdown-values")
async def get_dropdown_values(
    type: str = Query(..., description="Study type: PI or SD"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get distinct dropdown values for site, sponsor, and protocol for the current user.
    """
    return studies_service.get_dropdown_values(current_user, type)

@router.get("/getStudiesByUsername", response_model=List[StudyResponse])
async def get_studies_by_username(
    type: str = Query(..., description="Study type: PI or SD"),
    site: Optional[str] = Query(None),
    sponsor: Optional[str] = Query(None),
    protocol: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get studies by username and type (Protected endpoint), with optional filters for site, sponsor, and protocol.
    """
    return studies_service.get_studies_by_username(current_user, type, site, sponsor, protocol)

@router.get("/top-studies-risk-chart", response_model=Dict[str, Any])
async def get_top_studies_risk_chart(
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get top 10 studies vs risk score data for bar chart visualization
    """
    try:
        logger.info("Getting top studies risk chart data")
        result = studies_service.get_top_studies_risk_chart()
        logger.info(f"Top studies risk chart data retrieved successfully")
        return result
    except Exception as e:
        logger.error(f"Error getting top studies risk chart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get top studies risk chart: {str(e)}")

@router.get("/assessed-studies-highest-risk", response_model=Dict[str, Any])
async def get_assessed_studies_highest_risk(
    site: Optional[str] = Query(None, description="Filter by site"),
    sponsor: Optional[str] = Query(None, description="Filter by sponsor"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get top 10 assessed studies by highest risk for table visualization
    Optional filters for site, sponsor, and protocol
    """
    try:
        logger.info(f"Getting assessed studies by highest risk data with filters - site: {site}, sponsor: {sponsor}, protocol: {protocol}")
        result = studies_service.get_assessed_studies_highest_risk(site=site, sponsor=sponsor, protocol=protocol)
        logger.info(f"Assessed studies by highest risk data retrieved successfully")
        return result
    except Exception as e:
        logger.error(f"Error getting assessed studies by highest risk: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get assessed studies by highest risk: {str(e)}")

@router.get("/all-assessed-studies", response_model=Dict[str, Any])
async def get_all_assessed_studies(
    page: int = Query(1, description="Page number", ge=1),
    pageSize: int = Query(20, description="Records per page", ge=1, le=100),
    site: Optional[str] = Query(None, description="Filter by site"),
    sponsor: Optional[str] = Query(None, description="Filter by sponsor"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get all assessed studies with server-side pagination and filtering
    """
    try:
        logger.info(f"Getting all assessed studies - page: {page}, pageSize: {pageSize}, site: {site}, sponsor: {sponsor}, protocol: {protocol}")
        result = studies_service.get_all_assessed_studies(
            page=page, 
            page_size=pageSize, 
            site=site, 
            sponsor=sponsor, 
            protocol=protocol
        )
        logger.info(f"All assessed studies data retrieved successfully")
        return result
    except Exception as e:
        logger.error(f"Error getting all assessed studies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get all assessed studies: {str(e)}")

@router.get("/risk-table-filter-values", response_model=Dict[str, Any])
async def get_risk_table_filter_values(
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Get distinct values for risk table filter dropdowns
    """
    try:
        logger.info("Getting risk table filter values")
        result = studies_service.get_risk_table_filter_values()
        logger.info(f"Risk table filter values retrieved successfully")
        return result
    except Exception as e:
        logger.error(f"Error getting risk table filter values: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk table filter values: {str(e)}")

@router.get("/assessment-edit-permissions/{study_id}", response_model=Dict[str, Any])
async def get_assessment_edit_permissions(
    study_id: int,
    current_user: Dict[str, Any] = Depends(require_auth())
):
    """
    Check if the current user has edit permissions for a specific study assessment
    """
    try:
        logger.info(f"Checking edit permissions for study {study_id} for user {current_user.get('email')}")
        result = studies_service.get_assessment_edit_permissions(study_id, current_user)
        logger.info(f"Edit permissions check completed for study {study_id}")
        return result
    except Exception as e:
        logger.error(f"Error checking edit permissions for study {study_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check edit permissions: {str(e)}") 