#!/usr/bin/env python
"""
Create PostgreSQL database if it doesn't exist.
This script connects to the default 'postgres' database to create the ASCAI database.
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database configuration
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "kouekam"),
}

DB_NAME = os.environ.get("DB_NAME", "ASCAI")

def create_database():
    """Create the database if it doesn't exist."""
    print("=" * 60)
    print("Creating PostgreSQL Database")
    print("=" * 60)
    print(f"\nTarget database: {DB_NAME}")
    print(f"Connection: {DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
    try:
        # Connect to PostgreSQL server (use 'postgres' database to create new database)
        print("\nConnecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database="postgres"  # Connect to default database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        print(f"Checking if database '{DB_NAME}' exists...")
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"[OK] Database '{DB_NAME}' already exists!")
        else:
            print(f"Creating database '{DB_NAME}'...")
            # Create database with UTF8 encoding
            cursor.execute(f'CREATE DATABASE "{DB_NAME}" ENCODING \'UTF8\';')
            print(f"[OK] Database '{DB_NAME}' created successfully!")
        
        cursor.close()
        conn.close()
        
        # Test connection to the new database
        print(f"\nTesting connection to '{DB_NAME}'...")
        test_conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_NAME
        )
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT version();")
        version = test_cursor.fetchone()[0]
        print(f"[OK] Connection successful!")
        print(f"\nPostgreSQL Version: {version.split(',')[0]}")
        test_cursor.close()
        test_conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Connection failed!")
        print(f"Error: {str(e)}")
        print("\nTroubleshooting:")
        if "password" in str(e).lower() or "authentication" in str(e).lower():
            print("  • Password authentication failed")
            print("  • Check your DB_PASSWORD in .env file")
        elif "could not connect" in str(e).lower():
            print("  • Cannot connect to PostgreSQL server")
            print(f"  • Make sure PostgreSQL is running on {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_database()
    if success:
        print("\n" + "=" * 60)
        print("Next steps:")
        print("  1. Run migrations: python manage.py migrate")
        print("  2. Create superuser: python manage.py createsuperuser")
        print("  3. Run server: python manage.py runserver")
        print("=" * 60)
    sys.exit(0 if success else 1)

