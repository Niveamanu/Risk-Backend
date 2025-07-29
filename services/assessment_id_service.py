from typing import Dict, Any, Optional
from datetime import datetime
import logging
from database.connection import db

logger = logging.getLogger(__name__)

class AssessmentIDService:
    def __init__(self):
        # No schema name needed since we're using the actual table name
        pass
    
    def generate_assessment_id(self, study_id: int, assessment_date: str) -> str:
        """
        Generate a custom assessment ID in the format:
        [SiteCode]-[SponsorCode]-[ProtocolCode]-[AssessmentDate]-[Sequence]
        Example: FSA-CFP-CIN110112-20250220-001
        """
        try:
            # Get study information from riskassessment_site_study table
            study_query = """
                SELECT site, sponsor_code, protocol 
                FROM "Risk Assessment".riskassessment_site_study
                WHERE id = %s
            """
            study_result = db.execute_query(study_query, [study_id])
            
            if not study_result:
                raise ValueError(f"Study with ID {study_id} not found in riskassessment_site_study table")
            
            study = study_result[0]
            site_name = study.get('site', 'UNK')
            sponsor_code = study.get('sponsor_code', '')  # Empty string instead of 'UNK'
            protocol_full = study.get('protocol', 'UNK')
            protocol_code = protocol_full[:3] if protocol_full else 'UNK'  # Take first 3 characters
            
            # Create a shorter site code from the site name
            site_code = self._create_site_code(site_name)
            
            # Convert assessment date to YYYYMMDD format
            try:
                date_obj = datetime.strptime(assessment_date, '%Y-%m-%d')
                date_formatted = date_obj.strftime('%Y%m%d')
            except ValueError:
                # If date is already in YYYYMMDD format
                if len(assessment_date) == 8 and assessment_date.isdigit():
                    date_formatted = assessment_date
                else:
                    raise ValueError(f"Invalid date format: {assessment_date}. Expected YYYY-MM-DD or YYYYMMDD")
            
            # Get the next sequence number for this combination
            sequence = self._get_next_sequence(site_code, sponsor_code, protocol_code, date_formatted)
            
            # Generate the assessment ID (handle empty sponsor_code)
            if sponsor_code:
                assessment_id = f"{site_code}-{sponsor_code}-{protocol_code}-{date_formatted}-{sequence:03d}"
            else:
                assessment_id = f"{site_code}-{protocol_code}-{date_formatted}-{sequence:03d}"
            
            logger.info(f"Generated assessment ID: {assessment_id}")
            return assessment_id
            
        except Exception as e:
            logger.error(f"Error generating assessment ID: {str(e)}")
            raise
    
    def _create_site_code(self, site_name: str) -> str:
        """
        Create a short site code from the full site name
        """
        if not site_name or site_name == 'UNK':
            return 'UNK'
        
        # Remove common words and create abbreviation
        site_name_lower = site_name.lower().strip()
        
        # Handle common patterns
        if 'flourish' in site_name_lower:
            if 'san antonio' in site_name_lower:
                return 'FSA'
            elif 'san diego' in site_name_lower:
                return 'FSD'
            elif 'new york' in site_name_lower:
                return 'FNY'
            elif 'los angeles' in site_name_lower:
                return 'FLA'
            elif 'texas' in site_name_lower:
                return 'FTX'
            elif 'california' in site_name_lower:
                return 'FCA'
            else:
                # Generic Flourish site
                return 'FLR'
        
        # For other site names, take first letter of each word (up to 3 words)
        words = site_name.split()
        if len(words) == 1:
            return words[0][:3].upper()
        elif len(words) == 2:
            return (words[0][0] + words[1][:2]).upper()
        else:
            return (words[0][0] + words[1][0] + words[2][0]).upper()
    
    def _get_next_sequence(self, site_code: str, sponsor_code: str, protocol_code: str, date_formatted: str) -> int:
        """
        Get the next sequence number for assessments with the same site, sponsor, protocol, and date
        """
        try:
            # Check existing assessments with the same components
            existing_query = """
                SELECT assessment_id 
                FROM "Risk Assessment".assessments
                WHERE assessment_id LIKE %s
                ORDER BY assessment_id DESC
                LIMIT 1
            """
            if sponsor_code:
                pattern = f"{site_code}-{sponsor_code}-{protocol_code}-{date_formatted}-%"
            else:
                pattern = f"{site_code}-{protocol_code}-{date_formatted}-%"
            existing_result = db.execute_query(existing_query, [pattern])
            
            if not existing_result:
                return 1  # First assessment for this combination
            
            # Extract sequence number from the last assessment ID
            last_assessment_id = existing_result[0]['assessment_id']
            sequence_part = last_assessment_id.split('-')[-1]
            
            try:
                last_sequence = int(sequence_part)
                return last_sequence + 1
            except ValueError:
                logger.warning(f"Could not parse sequence number from {last_assessment_id}, starting from 1")
                return 1
                
        except Exception as e:
            logger.error(f"Error getting next sequence: {str(e)}")
            return 1  # Fallback to 1
    
    def parse_assessment_id(self, assessment_id: str) -> Dict[str, Any]:
        """
        Parse an assessment ID back into its components
        """
        try:
            parts = assessment_id.split('-')
            if len(parts) == 5:
                # Format: SITE-SPONSOR-PROTOCOL-DATE-SEQ
                site_code, sponsor_code, protocol_code, date_formatted, sequence = parts
            elif len(parts) == 4:
                # Format: SITE-PROTOCOL-DATE-SEQ (no sponsor)
                site_code, protocol_code, date_formatted, sequence = parts
                sponsor_code = ''
            else:
                raise ValueError(f"Invalid assessment ID format: {assessment_id}")
            
            # Convert date back to YYYY-MM-DD format
            try:
                date_obj = datetime.strptime(date_formatted, '%Y%m%d')
                assessment_date = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                assessment_date = date_formatted
            
            return {
                'site_code': site_code,
                'sponsor_code': sponsor_code,
                'protocol_code': protocol_code,
                'assessment_date': assessment_date,
                'sequence': int(sequence)
            }
            
        except Exception as e:
            logger.error(f"Error parsing assessment ID: {str(e)}")
            raise

# Global instance
assessment_id_service = AssessmentIDService() 