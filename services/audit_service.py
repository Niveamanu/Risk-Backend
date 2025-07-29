#!/usr/bin/env python3
"""
Audit Service for managing assessment audit trail
"""

from typing import Dict, List, Any, Optional
from fastapi import HTTPException
from database.connection import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self):
        self.schema_name = "Risk Assessment"
    
    def get_audit_trail_for_assessment(self, assessment_id: int, 
                                     field_name: Optional[str] = None,
                                     risk_factor_id: Optional[int] = None,
                                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit trail for an assessment with optional filtering
        """
        try:
            # Build the base query with risk factor names
            base_query = f"""
                SELECT 
                    aat.id,
                    aat.assessment_id,
                    aat.risk_factor_id,
                    rf.risk_factor_text,
                    aat.field_name,
                    aat.old_value,
                    aat.new_value,
                    aat.changed_by_name,
                    aat.changed_by_email,
                    aat.change_reason,
                    aat.changed_at
                FROM "{self.schema_name}".assessment_audit_trail aat
                LEFT JOIN "{self.schema_name}".risk_factors rf ON aat.risk_factor_id = rf.id
                WHERE aat.assessment_id = %s and aat.field_name  in ('Severity', 'Likelihood' )
            """
            
            params = [assessment_id]
    
            # Add field name filter
            if field_name:
                base_query += " AND aat.field_name = %s"
                params.append(field_name)
            
            # Add risk factor filter
            if risk_factor_id:
                base_query += " AND aat.risk_factor_id = %s"
                params.append(risk_factor_id)
            
            # Add ordering and limit
            base_query += " ORDER BY aat.changed_at DESC LIMIT %s"
            params.append(limit)
            
            result = db.execute_query(base_query, params)
            
            # Format the response in the desired structure
            formatted_result = []
            for row in result:
                formatted_result.append({
                    "id": row['id'],
                    "assessment_id": row['assessment_id'],
                    "risk_factor_id": row['risk_factor_id'],
                    "riskFactor": row['risk_factor_text'] or f"Risk Factor {row['risk_factor_id']}",
                    "field": row['field_name'],
                    "oldValue": row['old_value'],
                    "newValue": row['new_value'],
                    "changedBy": row['changed_by_name'],
                    "changedByEmail": row['changed_by_email'],
                    "changeReason": row['change_reason'],
                    "timestamp": row['changed_at'].strftime('%Y-%m-%d %I:%M %p') if row['changed_at'] else None
                })
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error getting audit trail for assessment {assessment_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve audit trail: {str(e)}")
    
    def get_severity_changes(self, assessment_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get only severity changes for an assessment
        """
        return self.get_audit_trail_for_assessment(assessment_id, field_name="Severity", limit=limit)
    
    def get_risk_score_changes(self, assessment_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get only risk score changes for an assessment
        """
        return self.get_audit_trail_for_assessment(assessment_id, field_name="Risk Score", limit=limit)
    
    def get_risk_level_changes(self, assessment_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get only risk level changes for an assessment
        """
        return self.get_audit_trail_for_assessment(assessment_id, field_name="Risk Level", limit=limit)
    
    def get_changes_by_user(self, assessment_id: int, user_email: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all changes made by a specific user for an assessment
        """
        try:
            query = f"""
                SELECT 
                    aat.id,
                    aat.assessment_id,
                    aat.risk_factor_id,
                    rf.risk_factor_code,
                    aat.field_name,
                    aat.old_value,
                    aat.new_value,
                    aat.changed_by_name,
                    aat.changed_by_email,
                    aat.change_reason,
                    aat.changed_at
                FROM "{self.schema_name}".assessment_audit_trail aat
                LEFT JOIN "{self.schema_name}".risk_factors rf ON aat.risk_factor_id = rf.id
                WHERE aat.assessment_id = %s AND LOWER(aat.changed_by_email) = LOWER(%s)
                ORDER BY aat.changed_at DESC LIMIT %s
            """
            
            result = db.execute_query(query, [assessment_id, user_email, limit])
            
            # Format the response
            formatted_result = []
            for row in result:
                formatted_result.append({
                    "id": row['id'],
                    "assessment_id": row['assessment_id'],
                    "risk_factor_id": row['risk_factor_id'],
                    "riskFactor": row['risk_factor_code'] or f"Risk Factor {row['risk_factor_id']}",
                    "field": row['field_name'],
                    "oldValue": row['old_value'],
                    "newValue": row['new_value'],
                    "changedBy": row['changed_by_name'],
                    "changedByEmail": row['changed_by_email'],
                    "changeReason": row['change_reason'],
                    "timestamp": row['changed_at'].strftime('%Y-%m-%d %I:%M %p') if row['changed_at'] else None
                })
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error getting changes by user for assessment {assessment_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve user changes: {str(e)}")
    
    def get_audit_summary(self, assessment_id: int) -> Dict[str, Any]:
        """
        Get a summary of audit data for an assessment
        """
        try:
            # Get total changes
            total_query = f"""
                SELECT COUNT(*) as total_changes
                FROM "{self.schema_name}".assessment_audit_trail
                WHERE assessment_id = %s
            """
            total_result = db.execute_query(total_query, [assessment_id])
            total_changes = total_result[0]['total_changes'] if total_result else 0
            
            # Get changes by field type
            field_query = f"""
                SELECT field_name, COUNT(*) as change_count
                FROM "{self.schema_name}".assessment_audit_trail
                WHERE assessment_id = %s
                GROUP BY field_name
                ORDER BY change_count DESC
            """
            field_result = db.execute_query(field_query, [assessment_id])
            
            # Get changes by user
            user_query = f"""
                SELECT changed_by_name, changed_by_email, COUNT(*) as change_count
                FROM "{self.schema_name}".assessment_audit_trail
                WHERE assessment_id = %s
                GROUP BY changed_by_name, changed_by_email
                ORDER BY change_count DESC
            """
            user_result = db.execute_query(user_query, [assessment_id])
            
            # Get latest change timestamp
            latest_query = f"""
                SELECT changed_at
                FROM "{self.schema_name}".assessment_audit_trail
                WHERE assessment_id = %s
                ORDER BY changed_at DESC
                LIMIT 1
            """
            latest_result = db.execute_query(latest_query, [assessment_id])
            latest_change = latest_result[0]['changed_at'] if latest_result else None
            
            return {
                "assessment_id": assessment_id,
                "total_changes": total_changes,
                "changes_by_field": [
                    {
                        "field": row['field_name'],
                        "count": row['change_count']
                    } for row in field_result
                ],
                "changes_by_user": [
                    {
                        "name": row['changed_by_name'],
                        "email": row['changed_by_email'],
                        "count": row['change_count']
                    } for row in user_result
                ],
                "latest_change": latest_change.strftime('%Y-%m-%d %I:%M %p') if latest_change else None
            }
            
        except Exception as e:
            logger.error(f"Error getting audit summary for assessment {assessment_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve audit summary: {str(e)}")
    
    def get_risk_factor_audit_trail(self, assessment_id: int, risk_factor_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit trail for a specific risk factor within an assessment
        """
        return self.get_audit_trail_for_assessment(assessment_id, risk_factor_id=risk_factor_id, limit=limit)

audit_service = AuditService() 