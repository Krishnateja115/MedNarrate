import sqlite3
import pprint

conn = sqlite3.connect("mednarrate.db")
c = conn.cursor()
c.execute("SELECT id, title, file_name, file_path, file_type, processing_status FROM reports WHERE file_type='image' AND processing_status='failed'")
rows = c.fetchall()
for row in rows:
    report_id = row[0]
    print(row)
    c.execute("SELECT error_reason, failure_category FROM report_analyses WHERE report_id=?", (report_id,))
    analysis = c.fetchone()
    print("  Analysis:", analysis)
conn.close()
