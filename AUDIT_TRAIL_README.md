# Assessment Audit Trail System

This document describes the implementation of the audit trail system for tracking changes to assessment risk data.

## Overview

The audit trail system automatically tracks all changes made to the `assessment_risks` table, including:
- **Severity changes** and their impact on risk scores
- **Likelihood changes** and their impact on risk scores  
- **Risk level changes** (Low/Medium/High)
- **Mitigation actions updates**
- **Custom notes changes**
- **Record creation and deletion**

## Database Schema

### Table: `assessment_audit_trail`

```sql
CREATE TABLE "Risk Assessment".assessment_audit_trail (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    risk_factor_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by_name VARCHAR(255),
    changed_by_email VARCHAR(255),
    change_reason TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_assessment_audit_assessment_id FOREIGN KEY (assessment_id) REFERENCES "Risk Assessment".assessments(id),
    CONSTRAINT fk_assessment_audit_risk_factor_id FOREIGN KEY (risk_factor_id) REFERENCES "Risk Assessment".risk_factors(id)
);
```

### Indexes for Performance

- `idx_assessment_audit_assessment_id` - For filtering by assessment
- `idx_assessment_audit_risk_factor_id` - For filtering by risk factor
- `idx_assessment_audit_changed_at` - For chronological queries
- `idx_assessment_audit_field_name` - For filtering by field type

## Database Triggers

### Trigger Function: `log_assessment_risk_changes()`

This PostgreSQL function automatically logs changes when:
- **INSERT**: New risk assessment created
- **UPDATE**: Any field modified (severity, likelihood, mitigation_actions, custom_notes)
- **DELETE**: Risk assessment deleted

### Key Features

1. **Automatic Risk Score Calculation**: When severity or likelihood changes, the trigger automatically calculates and logs the old and new risk scores
2. **Risk Level Tracking**: Automatically tracks when risk levels change from Low/Medium/High
3. **User Context**: Captures who made the change using session variables
4. **Comprehensive Logging**: Logs every field change with old and new values

## Implementation Details

### Files Created/Modified

1. **Database Migration**: `database/migrations/create_audit_trail_trigger.sql`
   - Creates audit trail table
   - Sets up indexes
   - Creates trigger function
   - Creates user context function

2. **Migration Script**: `run_audit_trail_migration.py`
   - Executes the database migration
   - Provides feedback on migration progress

3. **Audit Service**: `services/audit_service.py`
   - Business logic for querying audit trail
   - Methods for filtering and summarizing audit data

4. **Audit Router**: `api/v1/endpoints/audit_router.py`
   - REST API endpoints for audit trail access
   - Authentication and validation

5. **Assessment Service**: `services/assessment_service.py` (Modified)
   - Sets user context before database operations
   - Ensures audit trail captures user information

6. **Main App**: `main.py` (Modified)
   - Includes audit router in FastAPI app

## API Endpoints

### 1. Get Complete Audit Trail
```
GET /api/v1/audit-trail/{assessment_id}
```
Returns all audit entries for an assessment with optional filtering.

**Query Parameters:**
- `field_name` (optional): Filter by field type (e.g., 'severity', 'risk_score')
- `risk_factor_id` (optional): Filter by specific risk factor
- `limit` (default: 100): Maximum records to return

### 2. Get Severity Changes
```
GET /api/v1/audit-trail/{assessment_id}/severity-changes
```
Returns only severity-related changes.

### 3. Get Risk Score Changes
```
GET /api/v1/audit-trail/{assessment_id}/risk-score-changes
```
Returns only risk score changes (including those caused by severity/likelihood updates).

### 4. Get Risk Level Changes
```
GET /api/v1/audit-trail/{assessment_id}/risk-level-changes
```
Returns only risk level changes (Low/Medium/High transitions).

### 5. Get Changes by User
```
GET /api/v1/audit-trail/{assessment_id}/user-changes?user_email=user@example.com
```
Returns all changes made by a specific user.

### 6. Get Audit Summary
```
GET /api/v1/audit-trail/{assessment_id}/summary
```
Returns a summary of audit data including:
- Total number of changes
- Changes by field type
- Changes by user
- Latest change timestamp

### 7. Get Risk Factor Audit Trail
```
GET /api/v1/audit-trail/{assessment_id}/risk-factor/{risk_factor_id}
```
Returns audit trail for a specific risk factor within an assessment.

## Setup Instructions

### 1. Run Database Migration
```bash
python run_audit_trail_migration.py
```

### 2. Verify Installation
```bash
# Test the audit router
curl -X GET "http://localhost:8000/api/v1/audit-trail/test"
```

### 3. Test Audit Trail
```bash
# Get audit trail for assessment 80
curl -X GET "http://localhost:8000/api/v1/audit-trail/80" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get severity changes only
curl -X GET "http://localhost:8000/api/v1/audit-trail/80/severity-changes" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## How It Works

### 1. User Context Setting
Before any database operation, the application sets the current user context:
```python
context_query = f"""
    SELECT "Risk Assessment".set_current_user_context(%s, %s)
"""
db.execute_query(context_query, [user_name, user_email])
```

### 2. Automatic Trigger Execution
When data changes in `assessment_risks` table:
1. Trigger function `log_assessment_risk_changes()` fires
2. Captures old and new values
3. Calculates risk scores and levels
4. Logs changes to `assessment_audit_trail` table

### 3. Example Audit Trail Entry
When severity changes from 2 to 3 for risk factor 1 in assessment 80:
```json
{
  "id": 1,
  "assessment_id": 80,
  "risk_factor_id": 1,
  "field_name": "severity",
  "old_value": "2",
  "new_value": "3",
  "changed_by_name": "John Doe",
  "changed_by_email": "john.doe@example.com",
  "change_reason": "Severity updated",
  "changed_at": "2025-01-27T10:30:00Z"
}
```

Additional entries will be created for:
- Risk score change (4 → 6)
- Risk level change (Low → Medium) if applicable

## Risk Score Calculation

The trigger automatically calculates risk scores:
- **Risk Score = Severity × Likelihood**
- **Risk Level**:
  - Low: Score ≤ 4
  - Medium: Score 5-8  
  - High: Score ≥ 9

## Benefits

✅ **Complete Audit Trail**: Every change is automatically logged
✅ **User Accountability**: Know who made what changes and when
✅ **Risk Score Tracking**: Automatic calculation and logging of risk score changes
✅ **Performance Optimized**: Indexed queries for fast retrieval
✅ **Flexible Filtering**: Filter by field, user, risk factor, or time
✅ **Compliance Ready**: Meets regulatory requirements for change tracking

## Monitoring and Maintenance

### Performance Monitoring
- Monitor query performance on audit trail table
- Consider archiving old audit records if table grows large
- Use indexes for efficient filtering

### Data Integrity
- Foreign key constraints ensure data consistency
- Trigger ensures no changes are missed
- User context prevents anonymous changes

### Backup Considerations
- Include audit trail table in regular backups
- Consider separate backup strategy for audit data
- Implement retention policies for audit records

## Future Enhancements

1. **Email Notifications**: Alert users when critical changes are made
2. **Change Approval Workflow**: Require approval for high-risk changes
3. **Audit Report Generation**: PDF/Excel reports of audit trails
4. **Real-time Dashboard**: Live audit trail monitoring
5. **Advanced Analytics**: Trend analysis of risk changes over time

## Troubleshooting

### Common Issues

1. **Trigger Not Firing**: Check if trigger is properly installed
2. **Missing User Context**: Ensure `set_current_user_context()` is called
3. **Performance Issues**: Verify indexes are created and being used
4. **Permission Errors**: Check database user permissions for trigger execution

### Debug Queries

```sql
-- Check if trigger exists
SELECT * FROM information_schema.triggers 
WHERE trigger_name = 'trigger_assessment_risk_audit';

-- Check recent audit entries
SELECT * FROM "Risk Assessment".assessment_audit_trail 
ORDER BY changed_at DESC LIMIT 10;

-- Check trigger function
SELECT * FROM information_schema.routines 
WHERE routine_name = 'log_assessment_risk_changes';
``` 