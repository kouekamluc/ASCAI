#!/usr/bin/env python
"""
Test PostgreSQL database connection.
Run this script to verify your database configuration.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection
from django.conf import settings

def test_connection():
    """Test PostgreSQL database connection."""
    print("=" * 60)
    print("Testing PostgreSQL Database Connection")
    print("=" * 60)
    
    db_config = settings.DATABASES["default"]
    print(f"\nConfiguration:")
    print(f"  Engine: {db_config['ENGINE']}")
    print(f"  Database: {db_config['NAME']}")
    print(f"  User: {db_config['USER']}")
    print(f"  Host: {db_config['HOST']}")
    print(f"  Port: {db_config['PORT']}")
    print(f"  Password: {'*' * len(db_config['PASSWORD']) if db_config['PASSWORD'] else '(not set)'}")
    
    print(f"\nAttempting connection...")
    
    try:
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"[OK] Connection successful!")
            print(f"\nPostgreSQL Version:")
            print(f"  {version}")
            
            # Get database name
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            print(f"\nConnected to database: {db_name}")
            
            # Check if tables exist
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            table_count = cursor.fetchone()[0]
            print(f"  Tables in database: {table_count}")
            
            if table_count > 0:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name 
                    LIMIT 10;
                """)
                tables = [row[0] for row in cursor.fetchall()]
                print(f"  Sample tables: {', '.join(tables)}")
                if table_count > 10:
                    print(f"  ... and {table_count - 10} more")
            
            return True
            
    except Exception as e:
        print(f"\n[ERROR] Connection failed!")
        print(f"\nError: {str(e)}")
        print(f"\nTroubleshooting:")
        
        error_msg = str(e).lower()
        if "password" in error_msg or "authentication" in error_msg:
            print("  • Password authentication failed")
            print("  • Set DB_PASSWORD in your .env file or environment variables")
            print("  • Create .env file: cp env.example .env")
            print("  • Edit .env and set: DB_PASSWORD=your_postgres_password")
        elif "does not exist" in error_msg:
            print(f"  • Database '{db_config['NAME']}' does not exist")
            print("  • Create it in PostgreSQL:")
            print(f'    CREATE DATABASE "{db_config["NAME"]}" ENCODING \'UTF8\';')
        elif "could not connect" in error_msg or "connection refused" in error_msg:
            print(f"  • Cannot connect to PostgreSQL server")
            print(f"  • Make sure PostgreSQL is running")
            print(f"  • Check host: {db_config['HOST']}, port: {db_config['PORT']}")
        elif "timeout" in error_msg:
            print("  • Connection timeout")
            print("  • Check if PostgreSQL is running and accessible")
        else:
            print("  • Check your PostgreSQL configuration")
            print("  • Verify database credentials in .env file")
        
        print(f"\nFor more help, see env.example or README.md")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

