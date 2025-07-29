-- Create assessment_notifications table
CREATE TABLE IF NOT EXISTS "Risk Assessment".assessment_notifications (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    action_by_name VARCHAR(255) NOT NULL,
    action_by_email VARCHAR(255) NOT NULL,
    reason TEXT NOT NULL,
    comments TEXT,
    target_user_type VARCHAR(10) NOT NULL CHECK (target_user_type IN ('PI', 'SD')),
    study_id INTEGER NOT NULL,
    action_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_status BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_assessment_notifications_assessment_id ON "Risk Assessment".assessment_notifications(assessment_id);
CREATE INDEX IF NOT EXISTS idx_assessment_notifications_target_user_type ON "Risk Assessment".assessment_notifications(target_user_type);
CREATE INDEX IF NOT EXISTS idx_assessment_notifications_study_id ON "Risk Assessment".assessment_notifications(study_id);
CREATE INDEX IF NOT EXISTS idx_assessment_notifications_read_status ON "Risk Assessment".assessment_notifications(read_status);
CREATE INDEX IF NOT EXISTS idx_assessment_notifications_action_date ON "Risk Assessment".assessment_notifications(action_date);

-- Add foreign key constraints
ALTER TABLE "Risk Assessment".assessment_notifications 
ADD CONSTRAINT fk_assessment_notifications_assessment_id 
FOREIGN KEY (assessment_id) REFERENCES "Risk Assessment".assessments(id) ON DELETE CASCADE;

ALTER TABLE "Risk Assessment".assessment_notifications 
ADD CONSTRAINT fk_assessment_notifications_study_id 
FOREIGN KEY (study_id) REFERENCES "Risk Assessment".riskassessment_site_study(id) ON DELETE CASCADE;

-- Add comments to the table
COMMENT ON TABLE "Risk Assessment".assessment_notifications IS 'Stores notifications for assessment-related actions';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.id IS 'Primary key';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.assessment_id IS 'Reference to the assessment';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.action IS 'The action performed (e.g., Initial Save, Approved, Rejected, SD Created)';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.action_by_name IS 'Name of the person who performed the action';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.action_by_email IS 'Email of the person who performed the action';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.reason IS 'Reason for the action';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.comments IS 'Additional comments';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.target_user_type IS 'Who should receive this notification (PI or SD)';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.study_id IS 'Reference to the study';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.action_date IS 'When the action was performed';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.read_status IS 'Whether the notification has been read';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.created_at IS 'When the notification was created';
COMMENT ON COLUMN "Risk Assessment".assessment_notifications.updated_at IS 'When the notification was last updated'; 