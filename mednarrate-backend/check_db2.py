import sqlite3

conn = sqlite3.connect("mednarrate.db")
c = conn.cursor()
c.execute("SELECT id, title, file_name, file_path, file_type, processing_status FROM reports")
for row in c.fetchall():
    print(row)
conn.close()
