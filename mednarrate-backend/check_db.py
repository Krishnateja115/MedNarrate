import sqlite3
import json

conn = sqlite3.connect('mednarrate.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute('SELECT llm_provider, llm_model, error_reason, failure_category FROM report_analyses')
rows = c.fetchall()
for row in rows:
    print(dict(row))
