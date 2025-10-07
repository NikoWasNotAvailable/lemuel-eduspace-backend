"""
Database troubleshooting script
This script helps diagnose and fix enum-related database issues
"""

import asyncio
from sqlalchemy import text
from app.core.database import async_engine

async def fix_database_schema():
    """Fix database schema issues."""
    
    async with async_engine.begin() as conn:
        print("=== Database Schema Fix ===")
        
        # Check if users table exists
        result = await conn.execute(text("""
            SELECT TABLE_NAME 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'
        """))
        
        table_exists = result.fetchone() is not None
        print(f"Users table exists: {table_exists}")
        
        if table_exists:
            # Check current enum values
            print("\nChecking current ENUM values...")
            try:
                result = await conn.execute(text("""
                    SELECT COLUMN_TYPE 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'users' 
                    AND COLUMN_NAME = 'role'
                """))
                
                row = result.fetchone()
                if row:
                    print(f"Current role ENUM: {row[0]}")
                
                # Check if there are any users in the table
                result = await conn.execute(text("SELECT COUNT(*) FROM users"))
                count = result.scalar()
                print(f"Number of users in table: {count}")
                
                if count > 0:
                    # Show existing users and their roles
                    result = await conn.execute(text("SELECT id, name, role FROM users LIMIT 5"))
                    users = result.fetchall()
                    print("\nExisting users:")
                    for user in users:
                        print(f"  ID: {user[0]}, Name: {user[1]}, Role: {user[2]}")
                
            except Exception as e:
                print(f"Error checking table: {e}")
        
        # Drop and recreate the table with correct schema
        print("\n=== Recreating table with correct schema ===")
        
        # Drop the table if it exists
        await conn.execute(text("DROP TABLE IF EXISTS users"))
        print("Dropped existing users table")
        
        # Create the table with correct ENUM values
        create_table_sql = """
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nis VARCHAR(50) UNIQUE,
            password VARCHAR(255) NOT NULL,
            name VARCHAR(100) NOT NULL,
            role ENUM('admin', 'teacher', 'student', 'parent', 'student_parent') DEFAULT 'student',
            grade ENUM('TKA', 'TKB', 'SD1', 'SD2', 'SD3', 'SD4', 'SD5', 'SD6', 'SMP1', 'SMP2', 'SMP3') DEFAULT NULL,
            gender ENUM('male', 'female') DEFAULT NULL,
            email VARCHAR(100) UNIQUE,
            region VARCHAR(100) DEFAULT NULL,
            dob DATE DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        await conn.execute(text(create_table_sql))
        print("Created users table with correct ENUM values")
        
        # Create indexes
        await conn.execute(text("CREATE INDEX ix_users_id ON users (id)"))
        await conn.execute(text("CREATE INDEX ix_users_nis ON users (nis)"))
        await conn.execute(text("CREATE INDEX ix_users_email ON users (email)"))
        print("Created indexes")
        
        print("\n✅ Database schema fixed successfully!")
        print("You can now register users without enum errors.")

if __name__ == "__main__":
    asyncio.run(fix_database_schema())