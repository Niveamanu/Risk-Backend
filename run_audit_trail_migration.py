#!/usr/bin/env python3
"""
Script to run the audit trail migration for assessment_risks table
"""

import os
import sys
import re
from database.connection import db

def split_sql_statements(sql_script):
    """
    Split SQL script into individual statements, handling dollar-quoted strings properly
    """
    statements = []
    current_statement = ""
    in_dollar_quote = False
    dollar_quote_tag = ""
    brace_count = 0
    
    lines = sql_script.split('\n')
    
    for line in lines:
        current_statement += line + '\n'
        
        # Check for dollar-quoted strings
        if not in_dollar_quote:
            # Look for start of dollar quote
            dollar_match = re.search(r'\$([^$]*)\$', line)
            if dollar_match:
                in_dollar_quote = True
                dollar_quote_tag = dollar_match.group(1)
        else:
            # Look for end of dollar quote
            if f'${dollar_quote_tag}$' in line:
                in_dollar_quote = False
                dollar_quote_tag = ""
        
        # Only split on semicolons if not inside a dollar-quoted string
        if not in_dollar_quote and line.strip().endswith(';'):
            # Remove the semicolon from the end
            current_statement = current_statement.rstrip().rstrip(';')
            if current_statement.strip():
                statements.append(current_statement.strip())
            current_statement = ""
    
    # Add any remaining statement
    if current_statement.strip():
        statements.append(current_statement.strip())
    
    return statements

def run_audit_trail_migration():
    """
    Execute the audit trail migration
    """
    try:
        print("🔄 Starting audit trail migration...")
        
        # Read the migration SQL file
        migration_file = "database/migrations/create_audit_trail_trigger.sql"
        
        if not os.path.exists(migration_file):
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            sql_script = f.read()
        
        print("📄 Migration SQL loaded successfully")
        
        # Split the script into individual statements using proper parsing
        statements = split_sql_statements(sql_script)
        
        print(f"🔧 Executing {len(statements)} SQL statements...")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    print(f"  [{i}/{len(statements)}] Executing statement...")
                    # Add semicolon back for execution
                    db.execute_query(statement + ';')
                    print(f"  ✅ Statement {i} executed successfully")
                except Exception as e:
                    print(f"  ❌ Error executing statement {i}: {str(e)}")
                    print(f"  Statement: {statement[:100]}...")
                    return False
        
        print("🎉 Audit trail migration completed successfully!")
        print("\n📋 What was created:")
        print("  ✅ assessment_audit_trail table")
        print("  ✅ Database indexes for performance")
        print("  ✅ log_assessment_risk_changes() function")
        print("  ✅ trigger_assessment_risk_audit trigger")
        print("  ✅ set_current_user_context() function")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_audit_trail_migration()
    sys.exit(0 if success else 1) 