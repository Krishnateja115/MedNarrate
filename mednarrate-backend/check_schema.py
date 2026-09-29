import sqlite3

db_path = "mednarrate.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== analysis_translations columns ===")
cursor.execute("PRAGMA table_info(analysis_translations)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]:30s} type={col[2]:20s} notnull={col[3]} default={col[4]} pk={col[5]}")

print("\n=== alembic_version ===")
cursor.execute("SELECT version_num FROM alembic_version")
print(f"  Current version: {cursor.fetchall()}")

print("\n=== Row counts ===")
for table in ["reports", "report_analyses", "medications", "analysis_translations", "users"]:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:30s} count={count}")
    except Exception as e:
        print(f"  {table:30s} ERROR: {e}")

conn.close()
