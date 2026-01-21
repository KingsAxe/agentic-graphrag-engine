import os
import psycopg2
from dotenv import load_dotenv

# Load env to get connection string
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def reset_database():
    if not DB_URL:
        print("Error: DATABASE_URL not found in .env")
        return

    print("WARNING: This will DELETE ALL indexed documents and chat history.")
    confirm = input("Are you sure you want to proceed? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("Reset cancelled.")
        return

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # 1. Drop existing tables (Reverse Order of dependencies)
        print("Dropping old tables...")
        tables_to_drop = [
            "research_entries",      # The new table (if partial exists)
            "chat_history",          # The old history
            "langchain_pg_embedding",# The vectors
            "langchain_pg_collection"# The vector metadata
        ]
        
        for table in tables_to_drop:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            print(f"   - Dropped {table}")

        # 2. Re-apply the Masterpiece Schema
        print("🏗️  Applying new Schema...")
        schema_path = os.path.join("app", "database", "schema.sql")
        
        with open(schema_path, "r") as f:
            schema_sql = f.read()
            cur.execute(schema_sql)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database successfully reset and upgraded to Phase 3 Architecture.")

    except Exception as e:
        print(f"Database Reset Failed: {e}")

if __name__ == "__main__":
    reset_database()