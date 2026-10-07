import sqlite3
import json
import uuid

conn = sqlite3.connect('mednarrate.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Find report3
c.execute("SELECT * FROM reports WHERE file_name LIKE '%report3%' OR title LIKE '%report3%'")
report = c.fetchone()
if not report:
    print("report3 not found.")
else:
    print("--- REPORT ---")
    report_dict = dict(report)
    print("ID:", report_dict['id'])
    print("Title:", report_dict['title'])
    print("Type:", report_dict['report_type'])
    print("Path:", report_dict['file_path'])
    print("Extracted Length:", len(report_dict['extracted_text'] or ""))
    print("Extracted Content snippet:", repr(report_dict['extracted_text'][:200]) if report_dict['extracted_text'] else None)
    
    c.execute("SELECT * FROM report_analyses WHERE report_id = ?", (report_dict['id'],))
    analysis = c.fetchone()
    if analysis:
        print("\n--- ANALYSIS ---")
        analysis_dict = dict(analysis)
        labs_len = len(json.loads(analysis_dict['structured_lab_values'])) if analysis_dict['structured_lab_values'] else 0
        print("Structured Labs Count:", labs_len)
        print("Status:", report_dict['processing_status'])
        print("Provider:", analysis_dict['llm_provider'])
        print("Model:", analysis_dict['llm_model'])
        print("Verification Status:", analysis_dict['verification_status'])
        
        c.execute("SELECT language, schema_version FROM analysis_translations WHERE report_analysis_id = ?", (analysis_dict['id'],))
        translations = c.fetchall()
        print("\n--- TRANSLATIONS ---")
        for t in translations:
            print(dict(t))
    else:
        print("\nNo analysis found.")
