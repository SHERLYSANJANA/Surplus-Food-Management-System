
from db import get_connected

try:
    with get_connected() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            print("PostgreSQL:", cur.fetchone()[0])

            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            print("\nTables in your database:")
            for row in cur.fetchall():
                print("-", row[0])

    print("\nDatabase connection successful!")

except Exception as e:
    print("Connection failed:", repr(e))
