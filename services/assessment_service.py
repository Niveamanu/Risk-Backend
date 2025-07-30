from typing import List, Dict, Any
from database.connection import db
from fastapi import HTTPException
import logging
from datetime import datetime
from services.assessment_id_service import assessment_id_service
from services.notification_service import notification_service

logger = logging.getLogger(__name__)

# Schema name declaration
SCHEMA_NAME = "Risk Assessment"

class AssessmentService:
    def __init__(self):
        self.schema_name = SCHEMA_NAME
    
    def get_metadata(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get assessment sections and risk factors metadata
        """
        try:
            # Get assessment sections
            sections_query = f"""
                SELECT * FROM "{self.schema_name}".assessment_sections
                ORDER BY id
            """
            sections_data = db.execute_query(sections_query)
            
            # Get risk factors
            factors_query = f"""
                SELECT * FROM "{self.schema_name}".risk_factors
                WHERE is_active = true
                ORDER BY assessment_section_id, id
            """
            factors_data = db.execute_query(factors_query)
            
            # Convert to dictionaries and handle datetime
            sections = []
            for row in sections_data:
                section_dict = dict(row)
                for key, value in section_dict.items():
                    if hasattr(value, 'isoformat'):
                        section_dict[key] = value.isoformat()
                sections.append(section_dict)
            
            factors = []
            for row in factors_data:
                factor_dict = dict(row)
                for key, value in factor_dict.items():
                    if hasattr(value, 'isoformat'):
                        factor_dict[key] = value.isoformat()
                factors.append(factor_dict)
            
            return {
                "assessment_sections": sections,
                "risk_factors": factors
            }
            
        except Exception as e:
            logger.error(f"Metadata error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Metadata error: {str(e)}")
    
    def save_assessment(self, assessment_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save assessment data - creates assessment record and risk scores
        """
        try:
            # Extract data from assessment_data
            study_id = assessment_data.get("study_id")
            assessment_date = assessment_data.get("assessment_date")
            risk_scores = assessment_data.get("risk_scores", [])
            risk_mitigation_plans = assessment_data.get("risk_mitigation_plans", [])
            risk_dashboard = assessment_data.get("risk_dashboard")
            summary_comments = assessment_data.get("summary_comments", [])
            section_comments = assessment_data.get("section_comments", [])
            
            logger.info(f"Study ID: {study_id}")
            logger.info(f"Assessment date: {assessment_date}")
            logger.info(f"Risk scores count: {len(risk_scores)}")
            logger.info(f"Risk mitigation plans count: {len(risk_mitigation_plans)}")
            logger.info(f"Summary comments count: {len(summary_comments)}")
            logger.info(f"Section comments count: {len(section_comments)}")
            
            if not study_id or not assessment_date:
                raise HTTPException(status_code=400, detail="Study ID and assessment date are required")
            
            # Validate study_id exists
            study_check_query = """
                SELECT id FROM "Risk Assessment".riskassessment_site_study
                WHERE id = %s
            """
            study_result = db.execute_query(study_check_query, [study_id])
            if not study_result:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Study ID {study_id} does not exist in riskassessment_site_study table. Please provide a valid study ID."
                )
            
            user_name = current_user.get("name", "Unknown User")
            user_email = current_user.get("email", "unknown@email.com").lower() if current_user.get("email") else "unknown@email.com"
            
            # Validate risk factor IDs exist
            if risk_scores:
                risk_factor_ids = [score.get("risk_factor_id") for score in risk_scores if score.get("risk_factor_id")]
                logger.info(f"Risk factor IDs to validate: {risk_factor_ids}")
                if risk_factor_ids:
                    # Check if all risk factor IDs exist
                    risk_factors_query = f"""
                        SELECT id FROM "{self.schema_name}".risk_factors
                        WHERE id = ANY(%s) AND is_active = true
                    """
                    existing_risk_factors = db.execute_query(risk_factors_query, [risk_factor_ids])
                    existing_ids = {row['id'] for row in existing_risk_factors}
                    invalid_ids = set(risk_factor_ids) - existing_ids
                    
                    logger.info(f"Existing risk factor IDs: {existing_ids}")
                    logger.info(f"Invalid risk factor IDs: {invalid_ids}")
                    
                    if invalid_ids:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Invalid risk factor IDs: {list(invalid_ids)}. Please use valid risk factor IDs from the metadata endpoint."
                        )
            
            # Check if assessment already exists for this study
            existing_query = f"""
                SELECT id, assessment_id FROM "{self.schema_name}".assessments
                WHERE study_id = %s
            """
            existing_result = db.execute_query(existing_query, [study_id])
            
            if existing_result:
                # Update existing assessment
                assessment_id = existing_result[0]['id']
                custom_assessment_id = existing_result[0]['assessment_id']
                logger.info(f"Updating existing assessment with ID: {assessment_id}, Custom ID: {custom_assessment_id}")
                
                # Check current monitoring schedule BEFORE updating
                current_schedule_query = f"""
                    SELECT monitoring_schedule FROM "{self.schema_name}".assessments
                    WHERE id = %s
                """
                current_result = db.execute_query(current_schedule_query, [assessment_id])
                current_monitoring_schedule = None
                if current_result:
                    current_monitoring_schedule = current_result[0]['monitoring_schedule']
                    logger.info(f"Current monitoring schedule: {current_monitoring_schedule}")
                
                update_query = f"""
                    UPDATE "{self.schema_name}".assessments
                    SET 
                        assessment_date = %s,
                        next_review_date = %s,
                        monitoring_schedule = %s,
                        overall_risk_score = %s,
                        overall_risk_level = %s,
                        comments = %s,
                        status = 'Pending Review',
                        updated_by_name = %s,
                        updated_by_email = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                update_params = [
                    assessment_date,
                    assessment_data.get("next_review_date"),
                    assessment_data.get("monitoring_schedule"),
                    assessment_data.get("overall_risk_score"),
                    assessment_data.get("overall_risk_level"),
                    assessment_data.get("comments"),
                    user_name,
                    user_email,
                    assessment_id
                ]
                db.execute_query(update_query, update_params)
                
                # Store the current monitoring schedule for timeline tracking
                assessment_data['_current_monitoring_schedule'] = current_monitoring_schedule
                
                # Set user context for audit trail
                context_query = f"""
                    SELECT "Risk Assessment".set_current_user_context(%s, %s)
                """
                db.execute_query(context_query, [user_name, user_email])
                
                # Delete existing risk mitigation plans
                delete_plans_query = f"""
                    DELETE FROM "{self.schema_name}".assessment_risk_mitigation_plans
                    WHERE assessment_id = %s
                """
                deleted_plans = db.execute_query(delete_plans_query, [assessment_id])
                logger.info(f"Deleted {deleted_plans} existing risk mitigation plans for assessment {assessment_id}")
                
                # Delete existing risk dashboard
                delete_dashboard_query = f"""
                    DELETE FROM "{self.schema_name}".assessment_risk_dashboard
                    WHERE assessment_id = %s
                """
                deleted_dashboard = db.execute_query(delete_dashboard_query, [assessment_id])
                logger.info(f"Deleted {deleted_dashboard} existing risk dashboard for assessment {assessment_id}")
                
                # Delete existing summary comments
                delete_comments_query = f"""
                    DELETE FROM "{self.schema_name}".assessment_summary_comments
                    WHERE assessment_id = %s
                """
                deleted_comments = db.execute_query(delete_comments_query, [assessment_id])
                logger.info(f"Deleted {deleted_comments} existing summary comments for assessment {assessment_id}")
                
                # Delete existing section comments
                delete_section_comments_query = f"""
                    DELETE FROM "{self.schema_name}".section_comments
                    WHERE assessment_id = %s
                """
                deleted_section_comments = db.execute_query(delete_section_comments_query, [assessment_id])
                logger.info(f"Deleted {deleted_section_comments} existing section comments for assessment {assessment_id}")
                
                # Delete existing approval records to reset approval status
                delete_approvals_query = f"""
                    DELETE FROM "{self.schema_name}".assessment_approvals
                    WHERE assessment_id = %s
                """
                deleted_approvals = db.execute_query(delete_approvals_query, [assessment_id])
                logger.info(f"Deleted {deleted_approvals} existing approval records for assessment {assessment_id}")
                
            else:
                # Generate custom assessment ID
                custom_assessment_id = assessment_id_service.generate_assessment_id(study_id, assessment_date)
                logger.info(f"Generated custom assessment ID: {custom_assessment_id}")
                
                # Create new assessment
                logger.info("Creating new assessment")
                insert_query = f"""
                    INSERT INTO "{self.schema_name}".assessments
                    (study_id, assessment_id, conducted_by_name, conducted_by_email, assessment_date, 
                     next_review_date, monitoring_schedule, status, overall_risk_score, 
                     overall_risk_level, comments, updated_by_name, updated_by_email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                insert_params = [
                    study_id,
                    custom_assessment_id,
                    user_name,
                    user_email,
                    assessment_date,
                    assessment_data.get("next_review_date"),
                    assessment_data.get("monitoring_schedule"),
                    "In Progress",
                    assessment_data.get("overall_risk_score"),
                    assessment_data.get("overall_risk_level"),
                    assessment_data.get("comments"),
                    user_name,
                    user_email
                ]
                
                db.execute_query(insert_query, insert_params)
                
                # Get the newly created assessment ID
                get_id_query = f"""
                    SELECT id FROM "{self.schema_name}".assessments
                    WHERE study_id = %s AND assessment_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                id_result = db.execute_query(get_id_query, [study_id, custom_assessment_id])
                assessment_id = id_result[0]['id']
                logger.info(f"Created new assessment with ID: {assessment_id}, Custom ID: {custom_assessment_id}")
            
            # Set user context for audit trail (for new assessments)
            context_query = f"""
                SELECT "Risk Assessment".set_current_user_context(%s, %s)
            """
            db.execute_query(context_query, [user_name, user_email])
            
            # Timeline will be handled after summary comments are saved
            
            # Handle risk scores with UPDATE logic
            logger.info(f"Processing {len(risk_scores)} risk scores for assessment {assessment_id}")
            for i, risk_score in enumerate(risk_scores):
                risk_factor_id = risk_score.get("risk_factor_id")
                logger.info(f"Processing risk score {i+1} for risk factor {risk_factor_id}: {risk_score}")
                
                # Check if risk score already exists for this assessment and risk factor
                check_query = f"""
                    SELECT id FROM "{self.schema_name}".assessment_risks
                    WHERE assessment_id = %s AND risk_factor_id = %s
                """
                existing_result = db.execute_query(check_query, [assessment_id, risk_factor_id])
                
                if existing_result:
                    # Update existing risk score
                    logger.info(f"Updating existing risk score for risk factor {risk_factor_id}")
                    risk_update_query = f"""
                        UPDATE "{self.schema_name}".assessment_risks
                        SET severity = %s, likelihood = %s, risk_score = %s, 
                            risk_level = %s, mitigation_actions = %s, custom_notes = %s
                        WHERE assessment_id = %s AND risk_factor_id = %s
                    """
                    risk_params = [
                        risk_score.get("severity"),
                        risk_score.get("likelihood"),
                        risk_score.get("risk_score"),
                        risk_score.get("risk_level"),
                        risk_score.get("mitigation_actions"),
                        risk_score.get("custom_notes"),
                        assessment_id,
                        risk_factor_id
                    ]
                    logger.info(f"Risk update params: {risk_params}")
                    result = db.execute_query(risk_update_query, risk_params)
                    logger.info(f"Risk score {i+1} update result: {result}")
                else:
                    # Insert new risk score
                    logger.info(f"Inserting new risk score for risk factor {risk_factor_id}")
                    risk_insert_query = f"""
                        INSERT INTO "{self.schema_name}".assessment_risks
                        (assessment_id, risk_factor_id, severity, likelihood, risk_score, 
                         risk_level, mitigation_actions, custom_notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    risk_params = [
                        assessment_id,
                        risk_factor_id,
                        risk_score.get("severity"),
                        risk_score.get("likelihood"),
                        risk_score.get("risk_score"),
                        risk_score.get("risk_level"),
                        risk_score.get("mitigation_actions"),
                        risk_score.get("custom_notes")
                    ]
                    logger.info(f"Risk insert params: {risk_params}")
                    result = db.execute_query(risk_insert_query, risk_params)
                    logger.info(f"Risk score {i+1} insert result: {result}")
            
            # Insert risk mitigation plans
            logger.info(f"Inserting {len(risk_mitigation_plans)} risk mitigation plans for assessment {assessment_id}")
            for i, plan in enumerate(risk_mitigation_plans):
                logger.info(f"Inserting risk mitigation plan {i+1}: {plan}")
                plan_insert_query = f"""
                    INSERT INTO "{self.schema_name}".assessment_risk_mitigation_plans
                    (assessment_id, risk_item, responsible_person, mitigation_strategy, 
                     target_date, status, priority_level)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                plan_params = [
                    assessment_id,
                    plan.get("risk_item"),
                    plan.get("responsible_person"),
                    plan.get("mitigation_strategy"),
                    plan.get("target_date"),
                    plan.get("status", "Pending"),
                    plan.get("priority_level", "High")
                ]
                logger.info(f"Plan insert params: {plan_params}")
                result = db.execute_query(plan_insert_query, plan_params)
                logger.info(f"Risk mitigation plan {i+1} insert result: {result}")
            
            # Insert risk dashboard data
            if risk_dashboard:
                logger.info(f"Inserting risk dashboard data: {risk_dashboard}")
                dashboard_insert_query = f"""
                    INSERT INTO "{self.schema_name}".assessment_risk_dashboard
                    (assessment_id, total_risks, high_risk_count, medium_risk_count, 
                     low_risk_count, total_score, overall_risk_level, risk_level_criteria)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                dashboard_params = [
                    assessment_id,
                    risk_dashboard.get("total_risks", 0),
                    risk_dashboard.get("high_risk_count", 0),
                    risk_dashboard.get("medium_risk_count", 0),
                    risk_dashboard.get("low_risk_count", 0),
                    risk_dashboard.get("total_score", 0),
                    risk_dashboard.get("overall_risk_level"),
                    risk_dashboard.get("risk_level_criteria")
                ]
                logger.info(f"Dashboard insert params: {dashboard_params}")
                result = db.execute_query(dashboard_insert_query, dashboard_params)
                logger.info(f"Risk dashboard insert result: {result}")
            
            # Insert summary comments
            logger.info(f"Inserting {len(summary_comments)} summary comments for assessment {assessment_id}")
            for i, comment in enumerate(summary_comments):
                logger.info(f"Inserting summary comment {i+1}: {comment}")
                comment_insert_query = f"""
                    INSERT INTO "{self.schema_name}".assessment_summary_comments
                    (assessment_id, comment_type, comment_text, created_by_name, created_by_email)
                    VALUES (%s, %s, %s, %s, %s)
                """
                comment_params = [
                    assessment_id,
                    comment.get("comment_type"),
                    comment.get("comment_text"),
                    user_name,
                    user_email
                ]
                logger.info(f"Comment insert params: {comment_params}")
                result = db.execute_query(comment_insert_query, comment_params)
                logger.info(f"Summary comment {i+1} insert result: {result}")
            
            # Handle assessment timeline tracking after summary comments are saved
            self._handle_assessment_timeline(
                study_id=study_id,
                assessment_id=assessment_id,
                assessment_data=assessment_data,
                user_name=user_name,
                user_email=user_email,
                is_new_assessment=(not existing_result)
            )
            
            print("line no 337")
            print(f"Section comments: {section_comments}")
            print(f"Assessment ID: {assessment_id}")
            print("line no 339")
            # Insert section comments
            logger.info(f"Inserting {len(section_comments)} section comments for assessment {assessment_id}")
            for i, comment in enumerate(section_comments):
                logger.info(f"Inserting section comment {i+1}: {comment}")
                comment_insert_query = f"""
                    INSERT INTO "{self.schema_name}".section_comments
                    (assessment_id, section_key, section_title, comment_text)
                    VALUES (%s, %s, %s, %s)
                """
                comment_params = [
                    assessment_id,
                    comment.get("section_key"),
                    comment.get("section_title"),
                    comment.get("comment_text")
                ]
                logger.info(f"Section comment insert params: {comment_params}")
                result = db.execute_query(comment_insert_query, comment_params)
                logger.info(f"Section comment {i+1} insert result: {result}")
            
            # Get site director information for the study
            site_director_query = """
                SELECT site_director, site_director_email 
                FROM "Risk Assessment".riskassessment_site_study
                WHERE id = %s
            """
            site_director_result = db.execute_query(site_director_query, [study_id])
            
            if not site_director_result:
                logger.warning(f"Site director information not found for study {study_id}")
                site_director_name = "Unknown"
                site_director_email = "unknown@email.com"
            else:
                site_director_name = site_director_result[0]['site_director'] or "Unknown"
                site_director_email = site_director_result[0]['site_director_email'] or "unknown@email.com"
            
            logger.info(f"Site director: {site_director_name} ({site_director_email})")
            
            # Check if assessment approval record already exists
            existing_approval_query = f"""
                SELECT id FROM "{self.schema_name}".assessment_approvals
                WHERE assessment_id = %s
            """
            existing_approval_result = db.execute_query(existing_approval_query, [assessment_id])
            
            if existing_approval_result:
                # Delete existing approval record
                delete_approval_query = f"""
                    DELETE FROM "{self.schema_name}".assessment_approvals
                    WHERE assessment_id = %s
                """
                deleted_approval = db.execute_query(delete_approval_query, [assessment_id])
                logger.info(f"Deleted existing approval record for assessment {assessment_id}")
            
            # Insert new assessment approval record
            approval_insert_query = f"""
                INSERT INTO "{self.schema_name}".assessment_approvals
                (assessment_id, action, action_by_name, action_by_email, reason, comments, action_date)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """
            approval_params = [
                assessment_id,
                "Initial Save",  # Action will be updated in later steps
                site_director_name,
                site_director_email,
                "Assessment saved",  # Reason will be updated in later steps
                "Assessment data saved successfully"  # Comments will be updated in later steps
            ]
            
            approval_result = db.execute_query(approval_insert_query, approval_params)
            logger.info(f"Inserted assessment approval record: {approval_result}")
            
            # Ensure all changes are committed
            connection = db.get_connection()
            connection.commit()
            logger.info("All database changes committed")
            
            # Determine user type based on study information
            user_type = "PI"  # Default to PI
            try:
                # Check if user is PI or SD for this study
                study_user_query = """
                    SELECT 
                        CASE 
                            WHEN LOWER(principal_investigator_email) = LOWER(%s) THEN 'PI'
                            WHEN LOWER(site_director_email) = LOWER(%s) THEN 'SD'
                            ELSE 'PI'  -- Default to PI if not found
                        END as user_type
                    FROM "Risk Assessment".riskassessment_site_study
                    WHERE id = %s
                """
                user_type_result = db.execute_query(study_user_query, [user_email, user_email, study_id])
                if user_type_result:
                    user_type = user_type_result[0]['user_type']
                logger.info(f"Determined user type: {user_type} for user {user_email}")
            except Exception as e:
                logger.warning(f"Could not determine user type, defaulting to PI: {e}")
            
            # Create notification based on user type
            try:
                notification_result = notification_service.create_assessment_submission_notification(
                    assessment_id=assessment_id,
                    study_id=study_id,
                    submitter_name=user_name,
                    submitter_email=user_email,
                    submitter_type=user_type
                )
                logger.info(f"Created notification for {user_type} submission: {notification_result}")
            except Exception as notification_error:
                logger.warning(f"Failed to create notification: {notification_error}")
                # Don't fail the assessment save if notification fails
            
            # Return success immediately after saving
            logger.info(f"Assessment saved successfully with ID: {assessment_id}, Custom ID: {custom_assessment_id}")
            return {
                "message": "Assessment saved successfully",
                "assessment_id": assessment_id,
                "custom_assessment_id": custom_assessment_id,
                "study_id": study_id,
                "assessment_date": assessment_date,
                "risk_scores_count": len(risk_scores),
                "mitigation_plans_count": len(risk_mitigation_plans),
                "summary_comments_count": len(summary_comments),
                "section_comments_count": len(section_comments),
                "approval_record_created": True,
                "site_director_name": site_director_name,
                "site_director_email": site_director_email,
                "notification_created": True
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Save assessment error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Save assessment error: {str(e)}")

    def get_complete_assessment(self, assessment_id: int) -> Dict[str, Any]:
        """
        Get complete assessment data including risk scores, mitigation plans, dashboard, and comments
        """
        try:
            logger.info(f"=== GET COMPLETE ASSESSMENT START for ID: {assessment_id} ===")
            
            # Get basic assessment data
            assessment_query = f"""
                SELECT * FROM "{self.schema_name}".assessments
                WHERE id = %s
            """
            logger.info(f"Executing assessment query: {assessment_query}")
            assessment_result = db.execute_query(assessment_query, [assessment_id])
            logger.info(f"Assessment query result: {assessment_result}")
            
            if not assessment_result:
                raise HTTPException(status_code=404, detail=f"Assessment with ID {assessment_id} not found")
            
            assessment_data = dict(assessment_result[0])
            
            # Get risk scores
            risk_scores_query = f"""
                SELECT * FROM "{self.schema_name}".assessment_risks
                WHERE assessment_id = %s
                ORDER BY risk_factor_id
            """
            risk_scores_result = db.execute_query(risk_scores_query, [assessment_id])
            risk_scores = [dict(row) for row in risk_scores_result]
            
            # Get risk mitigation plans
            mitigation_plans_query = f"""
                SELECT * FROM "{self.schema_name}".assessment_risk_mitigation_plans
                WHERE assessment_id = %s
                ORDER BY id
            """
            mitigation_plans_result = db.execute_query(mitigation_plans_query, [assessment_id])
            mitigation_plans = [dict(row) for row in mitigation_plans_result]
            
            # Get risk dashboard data
            dashboard_query = f"""
                SELECT * FROM "{self.schema_name}".assessment_risk_dashboard
                WHERE assessment_id = %s
            """
            dashboard_result = db.execute_query(dashboard_query, [assessment_id])
            risk_dashboard = dict(dashboard_result[0]) if dashboard_result else None
            
            # Get summary comments
            summary_comments_query = f"""
                SELECT * FROM "{self.schema_name}".assessment_summary_comments
                WHERE assessment_id = %s
                ORDER BY created_at DESC
            """
            summary_comments_result = db.execute_query(summary_comments_query, [assessment_id])
            summary_comments = [dict(row) for row in summary_comments_result]
            
            # Get section comments
            section_comments_query = f"""
                SELECT * FROM "{self.schema_name}".section_comments
                WHERE assessment_id = %s
                ORDER BY id
            """
            section_comments_result = db.execute_query(section_comments_query, [assessment_id])
            section_comments = [dict(row) for row in section_comments_result]
            
            # Convert datetime objects to ISO format
            for key, value in assessment_data.items():
                if hasattr(value, 'isoformat'):
                    assessment_data[key] = value.isoformat()
            
            for risk_score in risk_scores:
                for key, value in risk_score.items():
                    if hasattr(value, 'isoformat'):
                        risk_score[key] = value.isoformat()
            
            for plan in mitigation_plans:
                for key, value in plan.items():
                    if hasattr(value, 'isoformat'):
                        plan[key] = value.isoformat()
            
            if risk_dashboard:
                for key, value in risk_dashboard.items():
                    if hasattr(value, 'isoformat'):
                        risk_dashboard[key] = value.isoformat()
            
            for comment in summary_comments:
                for key, value in comment.items():
                    if hasattr(value, 'isoformat'):
                        comment[key] = value.isoformat()
            
            for comment in section_comments:
                for key, value in comment.items():
                    if hasattr(value, 'isoformat'):
                        comment[key] = value.isoformat()
            
            complete_assessment = {
                "assessment": assessment_data,
                "risk_scores": risk_scores,
                "risk_mitigation_plans": mitigation_plans,
                "risk_dashboard": risk_dashboard,
                "summary_comments": summary_comments,
                "section_comments": section_comments
            }
            
            logger.info(f"=== GET COMPLETE ASSESSMENT END for ID: {assessment_id} ===")
            return complete_assessment
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting complete assessment: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting complete assessment: {str(e)}")

    def get_complete_assessment_by_study_id(self, study_id: int) -> Dict[str, Any]:
        """
        Get complete assessment data by study ID including risk scores, mitigation plans, dashboard, and comments
        """
        try:
            # First get the assessment ID for the study
            assessment_query = f"""
                SELECT id FROM "{self.schema_name}".assessments
                WHERE study_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """
            assessment_result = db.execute_query(assessment_query, [study_id])
            
            if not assessment_result:
                raise HTTPException(status_code=404, detail=f"No assessment found for study ID {study_id}")
            
            assessment_id = assessment_result[0]['id']
            return self.get_complete_assessment(assessment_id)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting complete assessment by study ID: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting complete assessment by study ID: {str(e)}")

    def save_assessment_draft(self, assessment_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save assessment data as draft - allows partial data with minimal validation
        """
        try:
            # Extract data from assessment_data
            study_id = assessment_data.get("study_id")
            assessment_date = assessment_data.get("assessment_date")
            risk_scores = assessment_data.get("risk_scores", [])
            risk_mitigation_plans = assessment_data.get("risk_mitigation_plans", [])
            risk_dashboard = assessment_data.get("risk_dashboard")
            summary_comments = assessment_data.get("summary_comments", [])
            section_comments = assessment_data.get("section_comments", [])
            
            logger.info(f"Draft save - Study ID: {study_id}")
            logger.info(f"Draft save - Risk scores count: {len(risk_scores)}")
            logger.info(f"Draft save - Section comments count: {len(section_comments)}")
            
            # Minimal validation for draft saves
            if not study_id:
                raise HTTPException(status_code=400, detail="Study ID is required for draft save")
            
            # Validate study_id exists
            study_check_query = """
                SELECT id FROM "Risk Assessment".riskassessment_site_study
                WHERE id = %s
            """
            study_result = db.execute_query(study_check_query, [study_id])
            if not study_result:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Study ID {study_id} does not exist"
                )
            
            user_name = current_user.get("name", "Unknown User")
            user_email = current_user.get("email", "unknown@email.com").lower() if current_user.get("email") else "unknown@email.com"
            
            # Check if assessment already exists for this study
            existing_query = f"""
                SELECT id, assessment_id FROM "{self.schema_name}".assessments
                WHERE study_id = %s
            """
            existing_result = db.execute_query(existing_query, [study_id])
            
            if existing_result:
                # Update existing assessment
                assessment_id = existing_result[0]['id']
                custom_assessment_id = existing_result[0]['assessment_id']
                logger.info(f"Updating existing draft assessment with ID: {assessment_id}")
                
                # Update assessment record
                update_query = f"""
                    UPDATE "{self.schema_name}".assessments
                    SET 
                        assessment_date = COALESCE(%s, assessment_date),
                        next_review_date = %s,
                        monitoring_schedule = %s,
                        overall_risk_score = %s,
                        overall_risk_level = %s,
                        comments = %s,
                        updated_by_name = %s,
                        updated_by_email = %s,
                        updated_at = CURRENT_TIMESTAMP,
                        status = 'In Progress'
                    WHERE id = %s
                """
                update_params = [
                    assessment_date,
                    assessment_data.get("next_review_date"),
                    assessment_data.get("monitoring_schedule"),
                    assessment_data.get("overall_risk_score"),
                    assessment_data.get("overall_risk_level"),
                    assessment_data.get("comments"),
                    user_name,
                    user_email,
                    assessment_id
                ]
                db.execute_query(update_query, update_params)
                
                # Set user context for audit trail
                context_query = f"""
                    SELECT "Risk Assessment".set_current_user_context(%s, %s)
                """
                db.execute_query(context_query, [user_name, user_email])
                
            else:
                # Generate custom assessment ID
                custom_assessment_id = assessment_id_service.generate_assessment_id(study_id, assessment_date or datetime.now().date())
                logger.info(f"Generated custom assessment ID for draft: {custom_assessment_id}")
                
                # Create new assessment
                insert_query = f"""
                    INSERT INTO "{self.schema_name}".assessments
                    (study_id, assessment_id, conducted_by_name, conducted_by_email, assessment_date, 
                     next_review_date, monitoring_schedule, status, overall_risk_score, 
                     overall_risk_level, comments, updated_by_name, updated_by_email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                insert_params = [
                    study_id,
                    custom_assessment_id,
                    user_name,
                    user_email,
                    assessment_date or datetime.now().date(),
                    assessment_data.get("next_review_date"),
                    assessment_data.get("monitoring_schedule"),
                    "In Progress",  # Always draft status
                    assessment_data.get("overall_risk_score"),
                    assessment_data.get("overall_risk_level"),
                    assessment_data.get("comments"),
                    user_name,
                    user_email
                ]
                
                db.execute_query(insert_query, insert_params)
                
                # Get the newly created assessment ID
                get_id_query = f"""
                    SELECT id FROM "{self.schema_name}".assessments
                    WHERE study_id = %s AND assessment_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                id_result = db.execute_query(get_id_query, [study_id, custom_assessment_id])
                assessment_id = id_result[0]['id']
                logger.info(f"Created new draft assessment with ID: {assessment_id}")
            
            # Set user context for audit trail (before any risk score operations)
            context_query = f"""
                SELECT "Risk Assessment".set_current_user_context(%s, %s)
            """
            db.execute_query(context_query, [user_name, user_email])
            
            # Handle risk scores - only save if provided
            if risk_scores:
                logger.info(f"Processing {len(risk_scores)} risk scores for draft assessment {assessment_id}")
                for risk_score in risk_scores:
                    if risk_score.get("risk_factor_id") and risk_score.get("severity") and risk_score.get("likelihood"):
                        risk_factor_id = risk_score.get("risk_factor_id")
                        logger.info(f"Processing risk score for risk factor {risk_factor_id}")
                        
                        # Check if risk score already exists for this assessment and risk factor
                        check_query = f"""
                            SELECT id FROM "{self.schema_name}".assessment_risks
                            WHERE assessment_id = %s AND risk_factor_id = %s
                        """
                        existing_result = db.execute_query(check_query, [assessment_id, risk_factor_id])
                        
                        if existing_result:
                            # Update existing risk score
                            logger.info(f"Updating existing risk score for risk factor {risk_factor_id}")
                            risk_update_query = f"""
                                UPDATE "{self.schema_name}".assessment_risks
                                SET severity = %s, likelihood = %s, risk_score = %s, 
                                    risk_level = %s, mitigation_actions = %s, custom_notes = %s
                                WHERE assessment_id = %s AND risk_factor_id = %s
                            """
                            risk_params = [
                                risk_score.get("severity"),
                                risk_score.get("likelihood"),
                                risk_score.get("risk_score"),
                                risk_score.get("risk_level"),
                                risk_score.get("mitigation_actions"),
                                risk_score.get("custom_notes"),
                                assessment_id,
                                risk_factor_id
                            ]
                            db.execute_query(risk_update_query, risk_params)
                        else:
                            # Insert new risk score
                            logger.info(f"Inserting new risk score for risk factor {risk_factor_id}")
                            risk_insert_query = f"""
                                INSERT INTO "{self.schema_name}".assessment_risks
                                (assessment_id, risk_factor_id, severity, likelihood, risk_score, 
                                 risk_level, mitigation_actions, custom_notes)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            risk_params = [
                                assessment_id,
                                risk_factor_id,
                                risk_score.get("severity"),
                                risk_score.get("likelihood"),
                                risk_score.get("risk_score"),
                                risk_score.get("risk_level"),
                                risk_score.get("mitigation_actions"),
                                risk_score.get("custom_notes")
                            ]
                            db.execute_query(risk_insert_query, risk_params)
            
            # Handle risk mitigation plans - only save if provided
            if risk_mitigation_plans:
                # Delete existing plans
                delete_plans_query = f"""
                    DELETE FROM "{self.schema_name}".assessment_risk_mitigation_plans
                    WHERE assessment_id = %s
                """
                db.execute_query(delete_plans_query, [assessment_id])
                
                # Insert new plans
                logger.info(f"Inserting {len(risk_mitigation_plans)} risk mitigation plans for draft")
                for plan in risk_mitigation_plans:
                    if plan.get("risk_item") or plan.get("responsible_person") or plan.get("mitigation_strategy"):
                        plan_insert_query = f"""
                            INSERT INTO "{self.schema_name}".assessment_risk_mitigation_plans
                            (assessment_id, risk_item, responsible_person, mitigation_strategy, 
                             target_date, status, priority_level)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        plan_params = [
                            assessment_id,
                            plan.get("risk_item"),
                            plan.get("responsible_person"),
                            plan.get("mitigation_strategy"),
                            plan.get("target_date"),
                            plan.get("status", "Pending"),
                            plan.get("priority_level", "High")
                        ]
                        db.execute_query(plan_insert_query, plan_params)
            
            # Handle risk dashboard - only save if provided
            if risk_dashboard:
                # Delete existing dashboard
                delete_dashboard_query = f"""
                    DELETE FROM "{self.schema_name}".assessment_risk_dashboard
                    WHERE assessment_id = %s
                """
                db.execute_query(delete_dashboard_query, [assessment_id])
                
                # Insert new dashboard
                dashboard_insert_query = f"""
                    INSERT INTO "{self.schema_name}".assessment_risk_dashboard
                    (assessment_id, total_risks, high_risk_count, medium_risk_count, 
                     low_risk_count, total_score, overall_risk_level, risk_level_criteria)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                dashboard_params = [
                    assessment_id,
                    risk_dashboard.get("total_risks", 0),
                    risk_dashboard.get("high_risk_count", 0),
                    risk_dashboard.get("medium_risk_count", 0),
                    risk_dashboard.get("low_risk_count", 0),
                    risk_dashboard.get("total_score", 0),
                    risk_dashboard.get("overall_risk_level"),
                    risk_dashboard.get("risk_level_criteria")
                ]
                db.execute_query(dashboard_insert_query, dashboard_params)
            
            # Handle summary comments - only save if provided
            if summary_comments:
                # Delete existing summary comments
                delete_comments_query = f"""
                    DELETE FROM "{self.schema_name}".assessment_summary_comments
                    WHERE assessment_id = %s
                """
                db.execute_query(delete_comments_query, [assessment_id])
                
                # Insert new summary comments
                logger.info(f"Inserting {len(summary_comments)} summary comments for draft")
                for comment in summary_comments:
                    if comment.get("comment_text"):
                        comment_insert_query = f"""
                            INSERT INTO "{self.schema_name}".assessment_summary_comments
                            (assessment_id, comment_type, comment_text, created_by_name, created_by_email)
                            VALUES (%s, %s, %s, %s, %s)
                        """
                        comment_params = [
                            assessment_id,
                            comment.get("comment_type"),
                            comment.get("comment_text"),
                            user_name,
                            user_email
                        ]
                        db.execute_query(comment_insert_query, comment_params)
            
            # Handle section comments - only save if provided
            if section_comments:
                # Delete existing section comments
                delete_section_comments_query = f"""
                    DELETE FROM "{self.schema_name}".section_comments
                    WHERE assessment_id = %s
                """
                db.execute_query(delete_section_comments_query, [assessment_id])
                
                # Insert new section comments
                logger.info(f"Inserting {len(section_comments)} section comments for draft")
                for comment in section_comments:
                    if comment.get("comment_text"):
                        comment_insert_query = f"""
                            INSERT INTO "{self.schema_name}".section_comments
                            (assessment_id, section_key, section_title, comment_text)
                            VALUES (%s, %s, %s, %s)
                        """
                        comment_params = [
                            assessment_id,
                            comment.get("section_key"),
                            comment.get("section_title"),
                            comment.get("comment_text")
                        ]
                        db.execute_query(comment_insert_query, comment_params)
            
            # Ensure all changes are committed
            connection = db.get_connection()
            connection.commit()
            logger.info("Draft assessment saved successfully")
            
            return {
                "message": "Draft assessment saved successfully",
                "assessment_id": assessment_id,
                "custom_assessment_id": custom_assessment_id,
                "study_id": study_id,
                "status": "In Progress",
                "risk_scores_count": len(risk_scores),
                "mitigation_plans_count": len(risk_mitigation_plans),
                "summary_comments_count": len(summary_comments),
                "section_comments_count": len(section_comments),
                "is_draft": True
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Draft save assessment error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Draft save assessment error: {str(e)}")

    def submit_final_assessment(self, assessment_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit final assessment - requires complete data and validation
        """
        try:
            # Use existing save_assessment logic but change status to "Completed"
            result = self.save_assessment(assessment_data, current_user)
            
            # Update status to completed
            assessment_id = result.get("assessment_id")
            if assessment_id:
                update_status_query = f"""
                    UPDATE "{self.schema_name}".assessments
                    SET status = 'Completed', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                db.execute_query(update_status_query, [assessment_id])
                
                connection = db.get_connection()
                connection.commit()
            
            result["status"] = "Completed"
            result["is_draft"] = False
            result["message"] = "Assessment submitted successfully"
            
            return result
            
        except Exception as e:
            logger.error(f"Submit final assessment error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Submit final assessment error: {str(e)}")

    def get_assessed_studies(self, current_user: Dict[str, Any], user_type: str = None) -> Dict[str, Any]:
        """
        Get all studies that have assessments with complete assessment data and approval info
        """
        try:
            user_email = current_user.get("email")
            print("912")
            print(user_email)
            print(user_type)
            if not user_email:
                raise HTTPException(status_code=400, detail="Email not found in token")
            user_email = user_email.lower()  # Convert to lowercase for consistent comparison
            
            logger.info(f"Starting get_assessed_studies for user: {user_email}, type: {user_type}")
            logger.info(f"Schema name: {self.schema_name}")
            
            # Build base query to get studies with assessments
            base_query = f"""
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
                    a.id as assessment_id,
                    a.study_id,
                    a.assessment_date,
                    a.next_review_date,
                    a.monitoring_schedule,
                    a.overall_risk_score,
                    a.overall_risk_level,
                    a.status as assessment_status,
                    a.conducted_by_name,
                    a.conducted_by_email,
                    a.updated_by_name as reviewed_by_name,
                    a.updated_by_email as reviewed_by_email,
                    a.comments,
                    a.created_at as assessment_created_at,
                    a.updated_at as assessment_updated_at,
                    s.crcname
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "{self.schema_name}".assessments a ON s.id = a.study_id
            """
            
            where_clauses = []
            params = []
            
            # Add user type filtering if specified
            if user_type:
                if user_type.upper() == "PI":
                    where_clauses.append("LOWER(s.principal_investigator_email) = LOWER(%s)")
                    params.append(user_email)
                elif user_type.upper() == "SD":
                    where_clauses.append("LOWER(s.site_director_email) = LOWER(%s)")
                    params.append(user_email)
                else:
                    raise HTTPException(status_code=400, detail="user_type must be 'PI' or 'SD'")
            
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            
            base_query += " ORDER BY s.id DESC, a.updated_at DESC"
            
            logger.info(f"Executing assessed studies query: {base_query}")
            logger.info(f"Query parameters: {params}")
            
            try:
                studies_data = db.execute_query(base_query, params)
                logger.info(f"Query executed successfully, found {len(studies_data)} studies")
            except Exception as query_error:
                logger.error(f"Database query error: {str(query_error)}")
                logger.error(f"Query: {base_query}")
                logger.error(f"Params: {params}")
                raise HTTPException(status_code=500, detail=f"Database query failed: {str(query_error)}")
            
            if not studies_data:
                logger.info("No studies found, returning empty result")
                return {"assessed_studies": []}
            
            assessed_studies = []
            
            for i, study_row in enumerate(studies_data):
                try:
                    study_id = study_row['id']
                    assessment_id = study_row['assessment_id']
                    
                    logger.info(f"Processing study {i+1}/{len(studies_data)}: ID={study_id}, Assessment ID={assessment_id}")
                    
                    # Get risk dashboard data
                    try:
                        dashboard_query = f"""
                            SELECT * FROM "{self.schema_name}".assessment_risk_dashboard
                            WHERE assessment_id = %s
                        """
                        dashboard_result = db.execute_query(dashboard_query, [assessment_id])
                        risk_dashboard = dict(dashboard_result[0]) if dashboard_result else None
                        logger.info(f"Dashboard data retrieved for assessment {assessment_id}")
                    except Exception as dashboard_error:
                        logger.error(f"Error getting dashboard for assessment {assessment_id}: {str(dashboard_error)}")
                        risk_dashboard = None
                    
                    # Get summary comments
                    try:
                        comments_query = f"""
                            SELECT * FROM "{self.schema_name}".assessment_summary_comments
                            WHERE assessment_id = %s
                            ORDER BY created_at DESC
                        """
                        comments_result = db.execute_query(comments_query, [assessment_id])
                        summary_comments = []
                        for comment_row in comments_result:
                            comment_dict = dict(comment_row)
                            # Convert datetime objects to ISO format
                            for key, value in comment_dict.items():
                                if hasattr(value, 'isoformat'):
                                    comment_dict[key] = value.isoformat()
                            summary_comments.append(comment_dict)
                        logger.info(f"Summary comments retrieved for assessment {assessment_id}: {len(summary_comments)} comments")
                    except Exception as comments_error:
                        logger.error(f"Error getting comments for assessment {assessment_id}: {str(comments_error)}")
                        summary_comments = []
                    
                    # Get assessment approval data
                    try:
                        approval_query = f"""
                            SELECT * FROM "{self.schema_name}".assessment_approvals
                            WHERE assessment_id = %s
                            ORDER BY action_date DESC
                            LIMIT 1
                        """
                        approval_result = db.execute_query(approval_query, [assessment_id])
                        approval_data = dict(approval_result[0]) if approval_result else None
                        logger.info(f"Approval data retrieved for assessment {assessment_id}")
                    except Exception as approval_error:
                        logger.error(f"Error getting approval data for assessment {assessment_id}: {str(approval_error)}")
                        approval_data = None
                    
                    # Convert datetime objects to ISO format for study data
                    study_dict = dict(study_row)
                    for key, value in study_dict.items():
                        if hasattr(value, 'isoformat'):
                            study_dict[key] = value.isoformat()
                    
                    # Build assessment data structure
                    assessment_data = {
                        "id": study_dict['assessment_id'],
                        "study_id": study_dict['study_id'],
                        "assessment_date": study_dict['assessment_date'],
                        "next_review_date": study_dict['next_review_date'],
                        "monitoring_schedule": study_dict['monitoring_schedule'],
                        "overall_risk_score": study_dict['overall_risk_score'],
                        "overall_risk_level": study_dict['overall_risk_level'],
                        "status": study_dict['assessment_status'],
                        "conducted_by_name": study_dict['conducted_by_name'],
                        "conducted_by_email": study_dict['conducted_by_email'],
                        "reviewed_by_name": study_dict['reviewed_by_name'],
                        "reviewed_by_email": study_dict['reviewed_by_email'],
                        "approved_by_name": None,
                        "approved_by_email": None,
                        "rejected_by_name": None,
                        "rejected_by_email": None,
                        "comments": study_dict['comments'],
                        "created_at": study_dict['assessment_created_at'],
                        "updated_at": study_dict['assessment_updated_at'],
                        "risk_dashboard": risk_dashboard,
                        "summary_comments": summary_comments,
                        "approval_data": approval_data,
                        "crcname": study_dict['crcname']
                    }
                    
                    # Populate approved/rejected by information from approval data
                    if approval_data:
                        if approval_data.get('action') == 'Approved':
                            assessment_data['approved_by_name'] = approval_data.get('action_by_name')
                            assessment_data['approved_by_email'] = approval_data.get('action_by_email')
                        elif approval_data.get('action') == 'Rejected':
                            assessment_data['rejected_by_name'] = approval_data.get('action_by_name')
                            assessment_data['rejected_by_email'] = approval_data.get('action_by_email')
                    
                    # Build final study structure
                    study_structure = {
                        "id": study_dict['id'],
                        "site": study_dict['site'],
                        "sponsor": study_dict['sponsor'],
                        "sponsor_code": study_dict['sponsor_code'],
                        "studyid": study_dict['studyid'],
                        "protocol": study_dict['protocol'],
                        "studytype": study_dict['studytype'],
                        "studytypetext": study_dict['studytypetext'],
                        "status": study_dict['status'],
                        "description": study_dict['description'],
                        "phase": study_dict['phase'],
                        "active": study_dict['active'],
                        "principal_investigator": study_dict['principal_investigator'],
                        "principal_investigator_email": study_dict['principal_investigator_email'],
                        "site_director": study_dict['site_director'],
                        "site_director_email": study_dict['site_director_email'],
                        "monitoring_schedule": study_dict['monitoring_schedule'],
                        "assessment_status": study_dict['assessment_status'],
                        "created_at": None,  # Studies table doesn't have these fields
                        "updated_at": None,  # Studies table doesn't have these fields
                        "assessment_data": assessment_data,
                        "crcname": study_dict['crcname']
                    }
                    
                    assessed_studies.append(study_structure)
                    logger.info(f"Successfully processed study {study_id}")
                    
                except Exception as study_error:
                    logger.error(f"Error processing study {i+1}: {str(study_error)}")
                    logger.error(f"Study row data: {study_row}")
                    # Continue processing other studies instead of failing completely
                    continue
            
            logger.info(f"Successfully processed {len(assessed_studies)} assessed studies")
            return {
                "assessed_studies": assessed_studies
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting assessed studies: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to get assessed studies: {str(e)}")

    def get_dashboard_stats(self, user_email: str, user_type: str) -> Dict[str, Any]:
        """
        Get dashboard statistics for PI or Site Director
        """
        try:
            # Ensure email is lowercase for consistent comparison
            user_email = user_email.lower() if user_email else ""
            logger.info(f"Calculating dashboard stats for {user_type}: {user_email}")
            
            # Build the base WHERE clause based on user type
            if user_type == "PI":
                where_clause = "LOWER(s.principal_investigator_email) = LOWER(%s)"
            elif user_type == "SD":
                where_clause = "LOWER(s.site_director_email) = LOWER(%s)"
            else:
                raise HTTPException(status_code=400, detail="user_type must be 'PI' or 'SD'")
            
            # 1. Total Active Sites (sites with active studies)
            active_sites_query = f"""
                SELECT COUNT(DISTINCT s.site) as count
                FROM "Risk Assessment".riskassessment_site_study s
                WHERE {where_clause} AND   s.active = 'true'
            """
            active_sites_result = db.execute_query(active_sites_query, [user_email])
            total_active_sites = active_sites_result[0]['count'] if active_sites_result else 0
            
            # 2. Total Active Studies (studies that are active)
            active_studies_query = f"""
                SELECT COUNT(*) as count
                FROM "Risk Assessment".riskassessment_site_study s
                WHERE {where_clause} AND  s.active = 'true'
            """
            active_studies_result = db.execute_query(active_studies_query, [user_email])
            total_active_studies = active_studies_result[0]['count'] if active_studies_result else 0
            
            # 3. Total Assessed Studies (studies that have assessments)
            assessed_studies_query = f"""
                SELECT COUNT(DISTINCT s.id) as count
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "{self.schema_name}".assessments a ON s.id = a.study_id
                WHERE {where_clause}
            """
            assessed_studies_result = db.execute_query(assessed_studies_query, [user_email])
            total_assessed_studies = assessed_studies_result[0]['count'] if assessed_studies_result else 0
            
            # 4. Total Approved Assessments (assessments with approval status)
            approved_assessments_query = f"""
                SELECT COUNT(DISTINCT a.id) as count
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "{self.schema_name}".assessments a ON s.id = a.study_id
                INNER JOIN "{self.schema_name}".assessment_approvals aa ON a.id = aa.assessment_id
                WHERE {where_clause} AND LOWER(aa.action) = 'approved'
            """
            approved_assessments_result = db.execute_query(approved_assessments_query, [user_email])
            total_approved_assessments = approved_assessments_result[0]['count'] if approved_assessments_result else 0
            
            # 5. Total Rejected Assessments (assessments with rejection status)
            rejected_assessments_query = f"""
                SELECT COUNT(DISTINCT a.id) as count
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "{self.schema_name}".assessments a ON s.id = a.study_id
                INNER JOIN "{self.schema_name}".assessment_approvals aa ON a.id = aa.assessment_id
                WHERE {where_clause} AND LOWER(aa.action) = 'rejected'
            """
            rejected_assessments_result = db.execute_query(rejected_assessments_query, [user_email])
            total_rejected_assessments = rejected_assessments_result[0]['count'] if rejected_assessments_result else 0
            
            # 6. Total Reviews Pending (assessments that need review/approval)
            pending_reviews_query = f"""
                SELECT COUNT(DISTINCT a.id) as count
                FROM "Risk Assessment".riskassessment_site_study s
                INNER JOIN "{self.schema_name}".assessments a ON s.id = a.study_id
                LEFT JOIN "{self.schema_name}".assessment_approvals aa ON a.id = aa.assessment_id
                WHERE {where_clause} 
                AND a.status = 'Completed' 
                AND (aa.id IS NULL OR LOWER(aa.action) NOT IN ('approved', 'rejected'))
            """
            pending_reviews_result = db.execute_query(pending_reviews_query, [user_email])
            total_reviews_pending = pending_reviews_result[0]['count'] if pending_reviews_result else 0
            
            logger.info(f"Dashboard stats calculated successfully for {user_type}: {user_email}")
            
            return {
                "total_active_sites": total_active_sites,
                "total_active_studies": total_active_studies,
                "total_assessed_studies": total_assessed_studies,
                "total_approved_assessments": total_approved_assessments,
                "total_rejected_assessments": total_rejected_assessments,
                "total_reviews_pending": total_reviews_pending,
                "user_type": user_type,
                "user_email": user_email
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calculating dashboard stats: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to calculate dashboard stats: {str(e)}")

    def _handle_assessment_timeline(
        self, 
        study_id: int, 
        assessment_id: int, 
        assessment_data: Dict[str, Any], 
        user_name: str, 
        user_email: str, 
        is_new_assessment: bool
    ) -> None:
        """
        Handle assessment timeline tracking - creates entries in assessment_timeline table
        """
        try:
            monitoring_schedule = assessment_data.get("monitoring_schedule")
            overall_risk_score = assessment_data.get("overall_risk_score")
            overall_risk_level = assessment_data.get("overall_risk_level")
            assessment_date = assessment_data.get("assessment_date")
            
            # Get the most recent comment_text from assessment_summary_comments
            comment_query = f"""
                SELECT comment_text 
                FROM "{self.schema_name}".assessment_summary_comments 
                WHERE assessment_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            comment_result = db.execute_query(comment_query, [assessment_id])
            final_comment = comment_result[0]['comment_text'] if comment_result else assessment_data.get("comments", "")
            
            if is_new_assessment:
                # First time - create initial assessment entry
                logger.info(f"Creating initial assessment timeline entry for assessment {assessment_id}")
                schedule_type = "Initial Assessment"
                
                timeline_insert_query = f"""
                    INSERT INTO "{self.schema_name}".assessment_timeline
                    (study_id, assessment_id, schedule_type, assessed_date, assessed_by_name, 
                     assessed_by_email, risk_score, risk_level, notes, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """
                timeline_params = [
                    study_id,
                    assessment_id,
                    schedule_type,
                    assessment_date,
                    user_name,
                    user_email,
                    overall_risk_score,
                    overall_risk_level,
                    final_comment or f"Initial assessment created by {user_name}"  # Use final comment or fallback
                ]
                
                db.execute_query(timeline_insert_query, timeline_params)
                logger.info(f"Initial assessment timeline entry created for assessment {assessment_id}")
                
            else:
                # Check if monitoring schedule has changed using stored current schedule
                current_monitoring_schedule = assessment_data.get('_current_monitoring_schedule')
                
                if current_monitoring_schedule is not None:
                    # Only create timeline entry if monitoring schedule has changed
                    if current_monitoring_schedule != monitoring_schedule:
                        logger.info(f"Monitoring schedule changed for assessment {assessment_id}")
                        logger.info(f"Old schedule: {current_monitoring_schedule}")
                        logger.info(f"New schedule: {monitoring_schedule}")
                        
                        # Create timeline entry for schedule change
                        schedule_type = f"Schedule Update: {monitoring_schedule}"
                        
                        timeline_insert_query = f"""
                            INSERT INTO "{self.schema_name}".assessment_timeline
                            (study_id, assessment_id, schedule_type, assessed_date, assessed_by_name, 
                             assessed_by_email, risk_score, risk_level, notes, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """
                        timeline_params = [
                            study_id,
                            assessment_id,
                            schedule_type,
                            assessment_date,
                            user_name,
                            user_email,
                            overall_risk_score,
                            overall_risk_level,
                            final_comment or f"Monitoring schedule updated from '{current_monitoring_schedule}' to '{monitoring_schedule}' by {user_name}"  # Use final comment or fallback
                        ]
                        
                        db.execute_query(timeline_insert_query, timeline_params)
                        logger.info(f"Schedule change timeline entry created for assessment {assessment_id}")
                    else:
                        logger.info(f"No monitoring schedule change for assessment {assessment_id} - no timeline entry needed")
                else:
                    logger.warning(f"Could not retrieve current monitoring schedule for assessment {assessment_id}")
                    
        except Exception as e:
            logger.error(f"Error handling assessment timeline: {str(e)}")
            # Don't fail the assessment save if timeline tracking fails
            logger.warning("Assessment timeline tracking failed, but assessment save will continue")

# Global instance of the service
assessment_service = AssessmentService() 