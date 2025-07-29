#!/usr/bin/env python3
"""
Database migration script to create the assessment_notifications table
"""

import os
import sys
from database.connection import db

def run_migration():
    """Run the migration to create the notifications table"""
    try:
        print("Starting migration: Creating assessment_notifications table...")
        
        # Read the migration SQL file
        migration_file = "database/migrations/create_notifications_table.sql"
        
        if not os.path.exists(migration_file):
            print(f"Error: Migration file not found: {migration_file}")
            sys.exit(1)
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("Executing migration SQL...")
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"Executing statement {i}/{len(statements)}...")
                try:
                    db.execute_query(statement)
                    print(f"✓ Statement {i} executed successfully")
                except Exception as e:
                    print(f"✗ Error executing statement {i}: {e}")
                    print(f"Statement: {statement[:100]}...")
                    raise
        
        print("✓ Migration completed successfully!")
        print("✓ assessment_notifications table created with all indexes and constraints")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration() 