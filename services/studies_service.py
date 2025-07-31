from typing import List, Dict, Any, Optional
from database.connection import db
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class StudiesService:
    def __init__(self):
        # No schema name needed since we're using the actual table name
        pass
    
    def get_studies_by_username(self, current_user: Dict[str, Any], user_type: str, site: str = None, sponsor: str = None, protocol: str = None) -> List[Dict[str, Any]]:
        """
        Get studies by username and type (PI or SD)
        
        Args:
            current_user (Dict[str, Any]): Current user data from token
            user_type (str): User type - 'PI' or 'SD'
            
        Returns:
            List[Dict[str, Any]]: List of studies matching the criteria
        """
        try:
            user_email = current_user.get("email")
            if not user_email:
                raise HTTPException(
                    status_code=400, 
                    detail="Email not found in token"
                )
            
            # Validate type parameter
            if user_type.upper() not in ["PI", "SD"]:
                raise HTTPException(
                    status_code=400, 
                    detail="Type must be either 'PI' or 'SD'"
                )
            
            logger.info(f"User {user_email} requesting studies with type: {user_type}")
            
            # Build WHERE clause
            if user_type.upper() == "PI":
                where_clauses = ["LOWER(s.principal_investigator_email) = LOWER(%s)"]
            else:
                where_clauses = ["LOWER(s.site_director_email) = LOWER(%s)"]
            params = [user_email]
            if site and site.lower() != "all":
                where_clauses.append("s.site = %s")
                params.append(site)
            if sponsor and sponsor.lower() != "all":
                where_clauses.append("s.sponsor = %s")
                params.append(sponsor)
            if protocol and protocol.lower() != "all":
                where_clauses.append("s.protocol = %s")
                params.append(protocol)
            where_sql = " AND ".join(where_clauses)
            query = f'''
                SELECT 
                    s.id,
                    s.siteid,
                    s.studyid,
                    s.site,
                    s.sponsor,
                    s.sponsor_code,
                    s.protocol,
                    s.studytype,
                    s.studytypetext,
                    s.status,
                    s.description,
                    s.phase,
                    s.active,
                    s.principal_investigator,
                    s.principal_investigator_email,
                    s.site_director,
                    s.site_director_email,
                    a.monitoring_schedule,
                    a.status as assessment_status,
                    s.crcname
                FROM "Risk Assessment".riskassessment_site_study s
                LEFT JOIN "Risk Assessment".assessments a ON s.id = a.study_id
                WHERE {where_sql} AND s.status != 'Inactive'
                ORDER BY s.id DESC
            '''
            
            # Execute query using the database connection
            studies_data = db.execute_query(query, params)
            
            # Convert RealDictCursor results to list of dictionaries
            studies = []
            for row in studies_data:
                study_dict = dict(row)
                # Convert datetime objects to strings for JSON serialization
                for key, value in study_dict.items():
                    if hasattr(value, 'isoformat'):
                        study_dict[key] = value.isoformat()
                studies.append(study_dict)
            
            logger.info(f"Found {len(studies)} studies for user {user_email} with type {user_type}")
            return studies
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Database error details: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def get_top_studies_risk_chart(self) -> Dict[str, Any]:
        """
        Get top 10 studies vs risk score data for bar chart visualization
        Returns data in the format: { label: 'Sponsor Protocol', value: risk_score, color: '#hex' }
        """
        try:
            logger.info("Getting top studies risk chart data")
            
            # Query to get top 10 studies with highest risk scores
            query = """
                SELECT 
                    s.sponsor,
                    s.protocol,
                    COALESCE(a.overall_risk_score, 0) as risk_score,
                    CONCAT(s.sponsor, ' ', s.protocol) as label
                FROM "Risk Assessment".riskassessment_site_study s
                LEFT JOIN "Risk Assessment".assessments a ON s.id = a.study_id
                WHERE a.overall_risk_score IS NOT NULL AND s.status != 'Inactive'
                ORDER BY a.overall_risk_score DESC
                LIMIT 10
            """
            
            results = db.execute_query(query)
            
            # Define colors for the bars
            colors = [
                '#7c6ee6',  # Purple
                '#4ed6fa',  # Light Blue
                '#ffb43a',  # Orange
                '#ff6b81',  # Pink/Red
                '#4ecdc4',  # Teal
                '#45b7d1',  # Blue
                '#96ceb4',  # Green
                '#feca57',  # Yellow
                '#ff9ff3',  # Pink
                '#54a0ff'   # Blue
            ]
            
            bar_chart_data = []
            for i, row in enumerate(results):
                # Use modulo to cycle through colors if more than 10 results
                color = colors[i % len(colors)]
                
                bar_chart_data.append({
                    "label": row['label'],
                    "value": int(row['risk_score']),
                    "color": color
                })
            
            logger.info(f"Generated bar chart data with {len(bar_chart_data)} entries")
            
            return {
                "barChartData": bar_chart_data,
                "totalStudies": len(bar_chart_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting top studies risk chart: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get top studies risk chart: {str(e)}")

    def get_assessed_studies_highest_risk(self, site: Optional[str] = None, sponsor: Optional[str] = None, protocol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get top 10 assessed studies by highest risk for table visualization
        Optional filters for site, sponsor, and protocol
        Returns data in the format: { 
            study_id: int, 
            site: 'Site Name', 
            sponsor: 'Sponsor Name', 
            protocol: 'Protocol Code', 
            study_type: 'Study Type Code',
            study_type_text: 'Study Type Description',
            description: 'Study Description',
            study_status: 'Study Status',
            phase: 'Study Phase',
            risk: risk_score, 
            assessment_id: int,
            monitoring_schedule: 'Schedule Type'
        }
        """
        try:
            logger.info(f"Getting assessed studies by highest risk data with filters - site: {site}, sponsor: {sponsor}, protocol: {protocol}")
            
            # Build the base query
            query = """
                SELECT 
                    s.id as study_id,
                    s.site,
                    s.sponsor,
                    s.protocol,
                    s.studytype as study_type,
                    s.studytypetext as study_type_text,
                    s.description,
                    s.status as study_status,
                    s.phase,
                    COALESCE(a.overall_risk_score, 0) as risk_score,
                    a.id as assessment_id,
                    a.monitoring_schedule,
                    s.crcname
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "Risk Assessment".assessments a ON s.id = a.study_id
                WHERE a.overall_risk_score IS NOT NULL AND s.status != 'Inactive'
            """
            
            # Add filters if provided
            params = []
            where_clauses = []
            
            if site:
                where_clauses.append("LOWER(s.site) = LOWER(%s)")
                params.append(site)
            
            if sponsor:
                where_clauses.append("LOWER(s.sponsor) = LOWER(%s)")
                params.append(sponsor)
            
            if protocol:
                where_clauses.append("LOWER(s.protocol) = LOWER(%s)")
                params.append(protocol)
            
            # Add WHERE clauses if any filters are provided
            if where_clauses:
                query += " AND " + " AND ".join(where_clauses)
            
            # Add ordering and limit
            query += " ORDER BY a.overall_risk_score DESC LIMIT 10"
            
            results = db.execute_query(query, params)
            
            risk_table_data = []
            for row in results:
                risk_table_data.append({
                    "study_id": row['study_id'],
                    "site": row['site'],
                    "sponsor": row['sponsor'],
                    "protocol": row['protocol'],
                    "study_type": row['study_type'],
                    "study_type_text": row['study_type_text'],
                    "description": row['description'] or "No description available",
                    "study_status": row['study_status'] or "Unknown",
                    "phase": row['phase'] or "Not specified",
                    "risk": int(row['risk_score']),
                    "assessment_id": row['assessment_id'],  # Additional field for potential "View Assessment" action
                    "monitoring_schedule": row['monitoring_schedule'] or "Not specified",
                    "crcname": row['crcname']
                })
            
            logger.info(f"Generated risk table data with {len(risk_table_data)} entries")
            
            return {
                "riskTableData": risk_table_data,
                "totalStudies": len(risk_table_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting assessed studies by highest risk: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get assessed studies by highest risk: {str(e)}")

    def get_dropdown_values(self, current_user: Dict[str, Any], user_type: str) -> Dict[str, list]:
        """
        Get distinct dropdown values for site, sponsor, and protocol for the current user.
        """
        try:
            user_email = current_user.get("email")
            if not user_email:
                raise HTTPException(status_code=400, detail="Email not found in token")
            user_email = user_email.lower()  # Convert to lowercase for consistent comparison
            if user_type.upper() not in ["PI", "SD"]:
                raise HTTPException(status_code=400, detail="Type must be either 'PI' or 'SD'")
            if user_type.upper() == "PI":
                where_clause = "LOWER(principal_investigator_email) = LOWER(%s)"
            else:
                where_clause = "LOWER(site_director_email) = LOWER(%s)"
            query = f'''
                SELECT DISTINCT site, sponsor, protocol
                FROM "Risk Assessment".riskassessment_site_study
                WHERE {where_clause} AND status != 'Inactive'
            '''
            params = [user_email]
            results = db.execute_query(query, params)
            sites = sorted({row['site'] for row in results if row['site']})
            sponsors = sorted({row['sponsor'] for row in results if row['sponsor']})
            protocols = sorted({row['protocol'] for row in results if row['protocol']})
            return {"sites": sites, "sponsors": sponsors, "protocols": protocols}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Dropdown DB error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Dropdown DB error: {str(e)}")

    def get_assessments_with_contacts(self, user_type: Optional[str], current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get assessments with contact information based on user type.
        Returns data in the format matching the frontend sampleAssessments structure.
        """
        try:
            user_email = current_user.get("email")
            if not user_email:
                raise HTTPException(status_code=400, detail="Email not found in token")
            user_email = user_email.lower()  # Convert to lowercase for consistent comparison
            
            # Build the base query
            base_query = '''
                SELECT 
                    a.id,
                    s.site,
                    s.sponsor,
                    s.protocol,
                    s.studytypetext as studyType,
                    s.description,
                    s.status as studyStatus,
                    s.phase,
                    a.monitoring_schedule as monitoringSchedule,
                    a.assessment_date as assessmentDate,
                    CASE 
                        WHEN a.overall_risk_score IS NOT NULL THEN 'Yes'
                        ELSE 'No'
                    END as scored,
                    COALESCE(a.overall_risk_score, 0) as totalRiskScore,
                    COALESCE(a.overall_risk_level, 'Not Assessed') as overallRisk,
                    COALESCE(a.status, 'Not Started') as assessmentStatus,
                    COALESCE(a.comments, 'No comments available.') as reason,
                    a.updated_at as lastUpdated,
                    COALESCE(a.conducted_by_name, 'Not specified') as conductedBy,
                    COALESCE(a.updated_by_name, 'Not specified') as reviewedBy,
                    CASE 
                        WHEN a.status = 'Approved' THEN a.updated_by_name
                        ELSE '-'
                    END as approvedBy,
                    CASE 
                        WHEN a.status = 'Rejected' THEN a.updated_by_name
                        ELSE '-'
                    END as rejectedBy,
                    s.principal_investigator_email,
                    s.site_director_email
                FROM "Risk Assessment".assessments a
                INNER JOIN "Risk Assessment".riskassessment_site_study s ON a.study_id = s.id
            '''
            
            where_clauses = []
            params = []
            
            # Add user type filtering
            if user_type:
                if user_type.upper() == "PI":
                    where_clauses.append("LOWER(s.principal_investigator_email) = LOWER(%s)")
                    params.append(user_email)
                elif user_type.upper() == "SITE_DIRECTOR":
                    where_clauses.append("LOWER(s.site_director_email) = LOWER(%s)")
                    params.append(user_email)
                else:
                    raise HTTPException(status_code=400, detail="user_type must be 'PI' or 'Site Director'")
            
            # Add status filter to exclude inactive studies
            where_clauses.append("s.status != 'Inactive'")

            # Add WHERE clause if needed
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            
            base_query += " ORDER BY a.updated_at DESC"
            
            logger.info(f"Executing query with user_type: {user_type}, user_email: {user_email}")
            results = db.execute_query(base_query, params)
            
            # Convert to the required format
            assessments = []
            for row in results:
                assessment = {
                    "id": row['id'],
                    "site": row['site'],
                    "sponsor": row['sponsor'],
                    "protocol": row['protocol'],
                    "studyType": row['studytype'],
                    "description": row['description'],
                    "studyStatus": row['studystatus'],
                    "phase": row['phase'],
                    "monitoringSchedule": row['monitoringschedule'],
                    "assessmentDate": row['assessmentdate'].isoformat() if row['assessmentdate'] else None,
                    "scored": row['scored'],
                    "totalRiskScore": row['totalriskscore'],
                    "overallRisk": row['overallrisk'],
                    "assessmentStatus": row['assessmentstatus'],
                    "reason": row['reason'],
                    "lastUpdated": row['lastupdated'].isoformat() if row['lastupdated'] else None,
                    "conductedBy": row['conductedby'],
                    "reviewedBy": row['reviewedby'],
                    "approvedBy": row['approvedby'],
                    "rejectedBy": row['rejectedby']
                }
                assessments.append(assessment)
            
            logger.info(f"Returning {len(assessments)} assessments")
            return assessments
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting assessments with contacts: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get assessments: {str(e)}")

    def get_studies(self) -> List[Dict[str, Any]]:
        """
        Get all studies
        """
        try:
            query = '''
                SELECT 
                    s.id,
                    s.siteid,
                    s.studyid,
                    s.site,
                    s.sponsor,
                    s.sponsor_code,
                    s.protocol,
                    s.studytype,
                    s.studytypetext,
                    s.status,
                    s.description,
                    s.phase,
                    s.active,
                    s.principal_investigator,
                    s.principal_investigator_email,
                    s.site_director,
                    s.site_director_email
                FROM "Risk Assessment".riskassessment_site_study s 
                WHERE s.status != 'Inactive'
                ORDER BY s.id DESC
            '''
            
            studies_data = db.execute_query(query)
            
            studies = []
            for row in studies_data:
                study_dict = dict(row)
                # Convert datetime objects to strings for JSON serialization
                for key, value in study_dict.items():
                    if hasattr(value, 'isoformat'):
                        study_dict[key] = value.isoformat()
                studies.append(study_dict)
            
            return studies
            
        except Exception as e:
            logger.error(f"Error getting studies: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get studies: {str(e)}")

    def get_all_assessed_studies(self, page: int = 1, page_size: int = 20, 
                                site: Optional[str] = None, sponsor: Optional[str] = None, 
                                protocol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all assessed studies with server-side pagination and filtering
        
        Args:
            page (int): Page number (default: 1)
            page_size (int): Records per page (default: 20)
            site (Optional[str]): Filter by site
            sponsor (Optional[str]): Filter by sponsor
            protocol (Optional[str]): Filter by protocol
            
        Returns:
            Dict[str, Any]: Paginated results with metadata
        """
        try:
            logger.info(f"Getting all assessed studies with pagination - page: {page}, page_size: {page_size}")
            
            # Build the base query with all required fields
            base_query = """
                SELECT 
                    s.id as study_id,
                    s.site,
                    s.sponsor,
                    s.protocol,
                    COALESCE(a.overall_risk_score, 0) as risk,
                    a.id as assessment_id,
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
                    a.status as assessment_status,
                    s.sponsor_code,
                    a.created_at,
                    s.crcname
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "Risk Assessment".assessments a ON s.id = a.study_id
                WHERE a.overall_risk_score IS NOT NULL AND s.status != 'Inactive'
            """
            
            # Build filter conditions
            filter_conditions = []
            params = []
            
            if site:
                filter_conditions.append("s.site = %s")
                params.append(site)
            
            if sponsor:
                filter_conditions.append("s.sponsor = %s")
                params.append(sponsor)
            
            if protocol:
                filter_conditions.append("s.protocol = %s")
                params.append(protocol)
            
            # Add filters to query
            if filter_conditions:
                base_query += " AND " + " AND ".join(filter_conditions)
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(*) as total
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "Risk Assessment".assessments a ON s.id = a.study_id
                WHERE a.overall_risk_score IS NOT NULL AND s.status != 'Inactive'
            """
            
            if filter_conditions:
                count_query += " AND " + " AND ".join(filter_conditions)
            
            count_result = db.execute_query(count_query, params)
            total_studies = count_result[0]['total'] if count_result else 0
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = (total_studies + page_size - 1) // page_size  # Ceiling division
            
            # Add ordering and pagination to main query
            base_query += " ORDER BY a.overall_risk_score DESC, a.created_at DESC LIMIT %s OFFSET %s"
            params.extend([page_size, offset])
            
            # Execute main query
            result = db.execute_query(base_query, params)
            
            # Format the response data
            risk_table_data = []
            for row in result:
                risk_table_data.append({
                    "study_id": row['study_id'],
                    "site": row['site'],
                    "sponsor": row['sponsor'],
                    "protocol": row['protocol'],
                    "risk": int(row['risk']),
                    "assessment_id": row['assessment_id'],
                    "study_type": row['study_type'],
                    "study_type_text": row['study_type_text'],
                    "description": row['description'],
                    "study_status": row['study_status'],
                    "phase": row['phase'],
                    "monitoring_schedule": row['monitoring_schedule'] or "Not specified",
                    "siteid": row['siteid'],
                    "studyid": row['studyid'],
                    "active": row['active'],
                    "principal_investigator": row['principal_investigator'],
                    "principal_investigator_email": row['principal_investigator_email'],
                    "site_director": row['site_director'],
                    "site_director_email": row['site_director_email'],
                    "assessment_status": row['assessment_status'],
                    "sponsor_code": row['sponsor_code'],
                    "created_at": row['created_at'].strftime('%Y-%m-%d') if row['created_at'] else None,
                    "crcname": row['crcname']
                })
            
            return {
                "riskTableData": risk_table_data,
                "totalStudies": total_studies,
                "totalPages": total_pages,
                "currentPage": page,
                "pageSize": page_size
            }
            
        except Exception as e:
            logger.error(f"Error getting all assessed studies: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get all assessed studies: {str(e)}")

    def get_risk_table_filter_values(self) -> Dict[str, Any]:
        """
        Get distinct values for risk table filter dropdowns
        
        Returns:
            Dict[str, Any]: Distinct values for sites, sponsors, and protocols
        """
        try:
            logger.info("Getting risk table filter values")
            
            # Get distinct sites
            sites_query = """
                SELECT DISTINCT s.site 
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "Risk Assessment".assessments a ON s.id = a.study_id
                WHERE s.site IS NOT NULL AND a.overall_risk_score IS NOT NULL AND s.status != 'Inactive'
                ORDER BY s.site
            """
            sites_result = db.execute_query(sites_query)
            sites = [row['site'] for row in sites_result]
            
            # Get distinct sponsors
            sponsors_query = """
                SELECT DISTINCT s.sponsor 
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "Risk Assessment".assessments a ON s.id = a.study_id
                WHERE s.sponsor IS NOT NULL AND a.overall_risk_score IS NOT NULL AND s.status != 'Inactive'
                ORDER BY s.sponsor
            """
            sponsors_result = db.execute_query(sponsors_query)
            sponsors = [row['sponsor'] for row in sponsors_result]
            
            # Get distinct protocols
            protocols_query = """
                SELECT DISTINCT s.protocol 
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "Risk Assessment".assessments a ON s.id = a.study_id
                WHERE s.protocol IS NOT NULL AND a.overall_risk_score IS NOT NULL AND s.status != 'Inactive'
                ORDER BY s.protocol
            """
            protocols_result = db.execute_query(protocols_query)
            protocols = [row['protocol'] for row in protocols_result]
            
            return {
                "sites": sites,
                "sponsors": sponsors,
                "protocols": protocols
            }
            
        except Exception as e:
            logger.error(f"Error getting risk table filter values: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get risk table filter values: {str(e)}")

    def get_assessment_edit_permissions(self, study_id: int, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the current user has edit permissions for a specific study assessment
        
        Args:
            study_id (int): The study ID to check permissions for
            current_user (Dict[str, Any]): Current user data from token
            
        Returns:
            Dict[str, Any]: Permission status with detailed information
        """
        try:
            user_email = current_user.get("email")
            if not user_email:
                raise HTTPException(status_code=400, detail="Email not found in token")
            
            logger.info(f"Checking edit permissions for study {study_id} for user {user_email}")
            
            # Check if study exists and get PI/SD information
            query = """
                SELECT 
                    s.principal_investigator_email as pi_email,
                    s.site_director_email as sd_email,
                    s.site,
                    s.sponsor,
                    s.protocol,
                    s.principal_investigator,
                    s.site_director
                FROM "Risk Assessment".riskassessment_site_study s
                WHERE s.id = %s AND s.status != 'Inactive'
            """
            
            result = db.execute_query(query, [study_id])
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Study with ID {study_id} not found")
            
            study_data = result[0]
            pi_email = study_data['pi_email']
            sd_email = study_data['sd_email']
            
            # Check if user is PI or SD
            is_pi = user_email.lower() == (pi_email.lower() if pi_email else "")
            is_sd = user_email.lower() == (sd_email.lower() if sd_email else "")
            can_edit = is_pi or is_sd
            
            # Determine reason
            if is_pi:
                reason = "User is Principal Investigator"
            elif is_sd:
                reason = "User is Site Director"
            else:
                reason = "User is not Principal Investigator or Site Director"
            
            # Build response
            response = {
                "canEdit": can_edit,
                "userEmail": user_email,
                "piEmail": pi_email,
                "sdEmail": sd_email,
                "reason": reason,
                "studyInfo": {
                    "studyId": study_id,
                    "site": study_data['site'],
                    "sponsor": study_data['sponsor'],
                    "protocol": study_data['protocol'],
                    "principalInvestigator": study_data['principal_investigator'],
                    "siteDirector": study_data['site_director']
                }
            }
            
            logger.info(f"Permission check result for study {study_id}: canEdit={can_edit}, reason='{reason}'")
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Error checking edit permissions for study {study_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to check edit permissions: {str(e)}")

# Global instance of the service
studies_service = StudiesService() 