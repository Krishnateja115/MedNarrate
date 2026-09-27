import sqlite3
conn = sqlite3.connect('mednarrate.db')
c = conn.cursor()
c.execute('SELECT provider, model_name, status, error_category, fallback_used FROM llm_diagnostic_events ORDER BY timestamp DESC LIMIT 20')
for row in c.fetchall():
    print(row)
conn.close()
