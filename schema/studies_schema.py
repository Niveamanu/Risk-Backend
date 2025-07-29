from pydantic import BaseModel
from typing import List, Optional

class StudyResponse(BaseModel):
    # Site information
    siteid: Optional[int] = None
    site: Optional[str] = None
    
    # Sponsor information
    sponsor: Optional[str] = None
    sponsor_code: Optional[str] = None
    
    # Study information
    id: int
    studyid: Optional[str] = None
    protocol: Optional[str] = None
    studytype: Optional[str] = None
    studytypetext: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    phase: Optional[str] = None
    active: Optional[bool] = None
    
    # Investigator information
    principal_investigator: Optional[str] = None
    principal_investigator_email: Optional[str] = None
    site_director: Optional[str] = None
    site_director_email: Optional[str] = None
    
    # Assessment information (nullable)
    monitoring_schedule: Optional[str] = None  # from assessment table
    assessment_status: Optional[str] = None    # from assessment table 