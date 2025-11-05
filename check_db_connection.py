#!/usr/bin/env python
"""
Database Connection Checker
Run this script to verify your PostgreSQL connection is configured correctly.
Usage: python check_db_connection.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.conf import settings

def check_database_connection():
    """Check if database connection is working."""
    print("=" * 60)
    print("PostgreSQL Connection Check")
    print("=" * 60)
    print()
    
    # Display configuration (without password)
    db_config = settings.DATABASES['default']
    print("Database Configuration:")
    print(f"  Engine: {db_config['ENGINE']}")
    print(f"  Name: {db_config['NAME']}")
    print(f"  User: {db_config['USER']}")
    print(f"  Host: {db_config['HOST']}")
    print(f"  Port: {db_config['PORT']}")
    print(f"  Password: {'*' * 10 if db_config['PASSWORD'] else '(not set)'}")
    print()
    
    # Test connection
    try:
        print("Testing connection...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"   PostgreSQL version: {version}")
            print()
            
            # Check database name
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            print(f"   Current database: {db_name}")
            print()
            
            # List tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print(f"   Tables in database: {len(tables)}")
            if tables:
                print("   First 10 tables:")
                for table in tables[:10]:
                    print(f"     - {table[0]}")
                if len(tables) > 10:
                    print(f"     ... and {len(tables) - 10} more")
            
            return True
            
    except Exception as e:
        print(f"❌ Connection failed!")
        print(f"   Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure PostgreSQL is running")
        print("  2. Check that the database 'ASCAI' exists")
        print("  3. Verify DB_PASSWORD is set correctly in .env file")
        print("  4. Ensure the user has proper permissions")
        print()
        print("To create the database, run in psql:")
        print('  CREATE DATABASE "ASCAI" ENCODING \'UTF8\';')
        return False

if __name__ == "__main__":
    success = check_database_connection()
    sys.exit(0 if success else 1)
