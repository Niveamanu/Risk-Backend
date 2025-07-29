-- Create assessment_audit_trail table if it doesn't exist
CREATE TABLE IF NOT EXISTS "Risk Assessment".assessment_audit_trail (
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_assessment_audit_assessment_id ON "Risk Assessment".assessment_audit_trail(assessment_id);
CREATE INDEX IF NOT EXISTS idx_assessment_audit_risk_factor_id ON "Risk Assessment".assessment_audit_trail(risk_factor_id);
CREATE INDEX IF NOT EXISTS idx_assessment_audit_changed_at ON "Risk Assessment".assessment_audit_trail(changed_at);
CREATE INDEX IF NOT EXISTS idx_assessment_audit_field_name ON "Risk Assessment".assessment_audit_trail(field_name);

-- Create a function to handle audit trail logging
CREATE OR REPLACE FUNCTION "Risk Assessment".log_assessment_risk_changes()
RETURNS TRIGGER AS $$
DECLARE
    old_risk_score INTEGER;
    new_risk_score INTEGER;
    old_risk_level VARCHAR(20);
    new_risk_level VARCHAR(20);
    current_user_name VARCHAR(255);
    current_user_email VARCHAR(255);
BEGIN
    -- Get current user information from session variables (set by application)
    current_user_name := COALESCE(current_setting('app.current_user_name', true), 'Unknown User');
    current_user_email := COALESCE(current_setting('app.current_user_email', true), 'unknown@email.com');
    
    -- Only handle UPDATE operations (no INSERT or DELETE logging)
    IF TG_OP = 'UPDATE' THEN
        -- Calculate old and new risk scores
        old_risk_score := OLD.severity * OLD.likelihood;
        new_risk_score := NEW.severity * NEW.likelihood;
        
        -- Calculate old and new risk levels
        old_risk_level := CASE 
            WHEN old_risk_score <= 4 THEN 'Low'
            WHEN old_risk_score <= 8 THEN 'Medium'
            ELSE 'High'
        END;
        
        new_risk_level := CASE 
            WHEN new_risk_score <= 4 THEN 'Low'
            WHEN new_risk_score <= 8 THEN 'Medium'
            ELSE 'High'
        END;
        
        -- Log severity changes ONLY if they are different
        IF OLD.severity IS DISTINCT FROM NEW.severity THEN
            INSERT INTO "Risk Assessment".assessment_audit_trail (
                assessment_id, risk_factor_id, field_name, old_value, new_value, 
                changed_by_name, changed_by_email, change_reason
            ) VALUES (
                NEW.assessment_id, NEW.risk_factor_id, 'Severity', 
                OLD.severity::TEXT, NEW.severity::TEXT,
                current_user_name, current_user_email, 'Severity updated'
            );
        END IF;
        
        -- Log likelihood changes ONLY if they are different
        IF OLD.likelihood IS DISTINCT FROM NEW.likelihood THEN
            INSERT INTO "Risk Assessment".assessment_audit_trail (
                assessment_id, risk_factor_id, field_name, old_value, new_value, 
                changed_by_name, changed_by_email, change_reason
            ) VALUES (
                NEW.assessment_id, NEW.risk_factor_id, 'Likelihood', 
                OLD.likelihood::TEXT, NEW.likelihood::TEXT,
                current_user_name, current_user_email, 'Likelihood updated'
            );
        END IF;
        
        -- Log risk score changes ONLY if they are different (due to severity or likelihood changes)
        IF old_risk_score != new_risk_score THEN
            INSERT INTO "Risk Assessment".assessment_audit_trail (
                assessment_id, risk_factor_id, field_name, old_value, new_value, 
                changed_by_name, changed_by_email, change_reason
            ) VALUES (
                NEW.assessment_id, NEW.risk_factor_id, 'Risk Score', 
                old_risk_score::TEXT, new_risk_score::TEXT,
                current_user_name, current_user_email, 'Risk score updated'
            );
        END IF;
        
        -- Log risk level changes ONLY if they are different
        IF old_risk_level != new_risk_level THEN
            INSERT INTO "Risk Assessment".assessment_audit_trail (
                assessment_id, risk_factor_id, field_name, old_value, new_value, 
                changed_by_name, changed_by_email, change_reason
            ) VALUES (
                NEW.assessment_id, NEW.risk_factor_id, 'Risk Level', 
                old_risk_level, new_risk_level,
                current_user_name, current_user_email, 'Risk level updated'
            );
        END IF;
        
        -- Log mitigation actions changes ONLY if they are different
        IF OLD.mitigation_actions IS DISTINCT FROM NEW.mitigation_actions THEN
            INSERT INTO "Risk Assessment".assessment_audit_trail (
                assessment_id, risk_factor_id, field_name, old_value, new_value, 
                changed_by_name, changed_by_email, change_reason
            ) VALUES (
                NEW.assessment_id, NEW.risk_factor_id, 'Mitigation Actions', 
                OLD.mitigation_actions, NEW.mitigation_actions,
                current_user_name, current_user_email, 'Mitigation actions updated'
            );
        END IF;
        
        -- Log custom notes changes ONLY if they are different
        IF OLD.custom_notes IS DISTINCT FROM NEW.custom_notes THEN
            INSERT INTO "Risk Assessment".assessment_audit_trail (
                assessment_id, risk_factor_id, field_name, old_value, new_value, 
                changed_by_name, changed_by_email, change_reason
            ) VALUES (
                NEW.assessment_id, NEW.risk_factor_id, 'Custom Notes', 
                OLD.custom_notes, NEW.custom_notes,
                current_user_name, current_user_email, 'Custom notes updated'
            );
        END IF;
        
        RETURN NEW;
    END IF;
    
    -- Handle INSERT operations (log initial values)
    IF TG_OP = 'INSERT' THEN
        -- Calculate initial risk score and level
        new_risk_score := NEW.severity * NEW.likelihood;
        new_risk_level := CASE 
            WHEN new_risk_score <= 4 THEN 'Low'
            WHEN new_risk_score <= 8 THEN 'Medium'
            ELSE 'High'
        END;
        
        -- Log initial severity
        INSERT INTO "Risk Assessment".assessment_audit_trail (
            assessment_id, risk_factor_id, field_name, old_value, new_value, 
            changed_by_name, changed_by_email, change_reason
        ) VALUES (
            NEW.assessment_id, NEW.risk_factor_id, 'Severity', 
            NULL, NEW.severity::TEXT,
            current_user_name, current_user_email, 'Initial severity set'
        );
        
        -- Log initial likelihood
        INSERT INTO "Risk Assessment".assessment_audit_trail (
            assessment_id, risk_factor_id, field_name, old_value, new_value, 
            changed_by_name, changed_by_email, change_reason
        ) VALUES (
            NEW.assessment_id, NEW.risk_factor_id, 'Likelihood', 
            NULL, NEW.likelihood::TEXT,
            current_user_name, current_user_email, 'Initial likelihood set'
        );
        
        -- Log initial risk score
        INSERT INTO "Risk Assessment".assessment_audit_trail (
            assessment_id, risk_factor_id, field_name, old_value, new_value, 
            changed_by_name, changed_by_email, change_reason
        ) VALUES (
            NEW.assessment_id, NEW.risk_factor_id, 'Risk Score', 
            NULL, new_risk_score::TEXT,
            current_user_name, current_user_email, 'Initial risk score calculated'
        );
        
        -- Log initial risk level
        INSERT INTO "Risk Assessment".assessment_audit_trail (
            assessment_id, risk_factor_id, field_name, old_value, new_value, 
            changed_by_name, changed_by_email, change_reason
        ) VALUES (
            NEW.assessment_id, NEW.risk_factor_id, 'Risk Level', 
            NULL, new_risk_level,
            current_user_name, current_user_email, 'Initial risk level calculated'
        );
        
        -- Log initial mitigation actions if provided
        IF NEW.mitigation_actions IS NOT NULL THEN
            INSERT INTO "Risk Assessment".assessment_audit_trail (
                assessment_id, risk_factor_id, field_name, old_value, new_value, 
                changed_by_name, changed_by_email, change_reason
            ) VALUES (
                NEW.assessment_id, NEW.risk_factor_id, 'Mitigation Actions', 
                NULL, NEW.mitigation_actions,
                current_user_name, current_user_email, 'Initial mitigation actions set'
            );
        END IF;
        
        -- Log initial custom notes if provided
        IF NEW.custom_notes IS NOT NULL THEN
            INSERT INTO "Risk Assessment".assessment_audit_trail (
                assessment_id, risk_factor_id, field_name, old_value, new_value, 
                changed_by_name, changed_by_email, change_reason
            ) VALUES (
                NEW.assessment_id, NEW.risk_factor_id, 'Custom Notes', 
                NULL, NEW.custom_notes,
                current_user_name, current_user_email, 'Initial custom notes set'
            );
        END IF;
        
        RETURN NEW;
    END IF;
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger on assessment_risks table
DROP TRIGGER IF EXISTS trigger_assessment_risk_audit ON "Risk Assessment".assessment_risks;
CREATE TRIGGER trigger_assessment_risk_audit
    AFTER INSERT OR UPDATE OR DELETE ON "Risk Assessment".assessment_risks
    FOR EACH ROW EXECUTE FUNCTION "Risk Assessment".log_assessment_risk_changes();

-- Create a function to set current user context (to be called by application)
CREATE OR REPLACE FUNCTION "Risk Assessment".set_current_user_context(user_name VARCHAR(255), user_email VARCHAR(255))
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_name', user_name, false);
    PERFORM set_config('app.current_user_email', user_email, false);
END;
$$ LANGUAGE plpgsql; 