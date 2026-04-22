import sqlite3
import os

db_path = 'job_intelligence.db'

if os.path.exists(db_path):
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(job_listings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'skills' not in columns:
            print("Adding 'skills' column...")
            cursor.execute("ALTER TABLE job_listings ADD COLUMN skills TEXT")
            conn.commit()
            print("Column 'skills' added successfully.")
        else:
            print("Column 'skills' already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()
else:
    print("Database file not found. Re-run pipeline to create it.")
