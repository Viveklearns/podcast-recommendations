#!/usr/bin/env python3
"""Test PostgreSQL connection"""
import psycopg2

POSTGRES_URL = "postgresql://podbooks_db_user:6eSXjFNwNvqX8RqNo91J2YbmrXgHv3PW@dpg-d54vc00gjchc73862ubg-a.oregon-postgres.render.com/podbooks_db"

# Parse URL
# postgresql://user:pass@host/db
parts = POSTGRES_URL.replace("postgresql://", "").split("@")
userpass = parts[0].split(":")
hostdb = parts[1].split("/")

user = userpass[0]
password = userpass[1]
host = hostdb[0]
database = hostdb[1]

print(f"Connecting to {host}/{database} as {user}...")

try:
    conn = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        connect_timeout=10
    )
    print("✅ Connected successfully!")

    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0]}")

    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    tables = cursor.fetchall()
    print(f"\nTables in database: {[t[0] for t in tables]}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Connection failed: {e}")
