import sqlite3
import json

db_path = "mednarrate.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Users (email, id) ===")
cursor.execute("SELECT id, email FROM users LIMIT 5")
for u in cursor.fetchall():
    print(f"  id={u[0]} email={u[1]}")

print("\n=== Reports with analyses (id, title, user_id) ===")
cursor.execute("""
    SELECT r.id, r.title, r.user_id, ra.id as analysis_id, ra.patient_summary, ra.abnormal_findings
    FROM reports r
    LEFT JOIN report_analyses ra ON r.id = ra.report_id
    WHERE ra.id IS NOT NULL
    LIMIT 5
""")
reports = cursor.fetchall()
for r in reports:
    rid, title, uid, raid, psummary, findings = r
    findings_list = json.loads(findings) if findings else []
    test_flags = [(f.get("test_name","?"), f.get("flag","?"), f.get("value","?")) for f in findings_list[:5]]
    print(f"  report_id={rid}")
    print(f"    title={title}")
    print(f"    user_id={uid}")
    print(f"    analysis_id={raid}")
    print(f"    summary_len={len(psummary or '')}")
    print(f"    findings_sample={test_flags}")

print("\n=== Existing analysis_translations ===")
cursor.execute("SELECT report_analysis_id, language, schema_version, patient_summary FROM analysis_translations")
for t in cursor.fetchall():
    print(f"  analysis_id={t[0]} lang={t[1]} schema_ver={t[2]} summary_len={len(t[3] or '')}")

conn.close()
