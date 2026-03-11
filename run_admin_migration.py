"""
Run this once to add admin support + global exercises fields in Supabase.
Uses DATABASE_URL from .env (direct Postgres connection).

Steps:
1) Set DATABASE_URL in .env:
   DATABASE_URL=postgresql://postgres.PROJECT_REF:YOUR_DB_PASSWORD@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
2) Run:
   python run_admin_migration.py
"""
import os
import sys
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv

    load_dotenv(env_path)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL or "YOUR_DB_PASSWORD" in DATABASE_URL:
    print("ERROR: DATABASE_URL is missing or still has YOUR_DB_PASSWORD placeholder.")
    print("Update .env DATABASE_URL with your Supabase DB password, then re-run.")
    sys.exit(1)

sql_path = Path(__file__).resolve().parent / "supabase_admin_dashboard.sql"
if not sql_path.exists():
    print("ERROR: supabase_admin_dashboard.sql not found.")
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    print("Install psycopg2: pip install psycopg2-binary")
    sys.exit(1)


def main():
    ddl = sql_path.read_text(encoding="utf-8")
    print("Connecting to Supabase Postgres...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        print("Running admin migration SQL...")
        cur.execute(ddl)
        print("Done. Admin columns are ready.")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()

