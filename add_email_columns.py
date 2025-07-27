#!/usr/bin/env python3
"""
Migration script to add email tracking columns to avatar_requests table.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set!")
    sys.exit(1)

def add_email_columns():
    """Add email_requested and email_request_time columns to avatar_requests table."""
    print("=" * 60)
    print("Adding email columns to avatar_requests table")
    print("=" * 60)
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'avatar_requests' 
                AND column_name IN ('email_requested', 'email_request_time')
            """)).fetchall()
            
            existing_columns = [row[0] for row in result]
            print(f"Existing columns: {existing_columns}")
            
            # Add email_requested column if it doesn't exist
            if 'email_requested' not in existing_columns:
                print("\nAdding email_requested column...")
                conn.execute(text("""
                    ALTER TABLE avatar_requests 
                    ADD COLUMN email_requested BOOLEAN DEFAULT FALSE NOT NULL
                """))
                conn.commit()
                print("✅ Added email_requested column")
            else:
                print("⚠️  email_requested column already exists")
            
            # Add email_request_time column if it doesn't exist
            if 'email_request_time' not in existing_columns:
                print("\nAdding email_request_time column...")
                conn.execute(text("""
                    ALTER TABLE avatar_requests 
                    ADD COLUMN email_request_time TIMESTAMP NULL
                """))
                conn.commit()
                print("✅ Added email_request_time column")
            else:
                print("⚠️  email_request_time column already exists")
            
            # Verify columns were added
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'avatar_requests' 
                AND column_name IN ('email_requested', 'email_request_time')
                ORDER BY column_name
            """)).fetchall()
            
            print("\n" + "-" * 40)
            print("Email columns in avatar_requests table:")
            for col_name, data_type, is_nullable in result:
                print(f"  - {col_name}: {data_type} (nullable: {is_nullable})")
            
            print("\n✅ Migration completed successfully!")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    
    finally:
        engine.dispose()
    
    print("=" * 60)

if __name__ == "__main__":
    add_email_columns()