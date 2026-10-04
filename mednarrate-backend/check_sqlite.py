import sqlite3

def check_db():
    conn = sqlite3.connect('mednarrate.db')
    cursor = conn.cursor()
    cursor.execute("SELECT language, findings_json FROM analysis_translation")
    rows = cursor.fetchall()
    for row in rows:
        lang = row[0]
        findings_json = row[1]
        print(f"Language: {lang}, Findings JSON length: {len(findings_json) if findings_json else 0}")
        if findings_json:
            print(f"Content preview: {findings_json[:100]}")
    conn.close()

if __name__ == "__main__":
    check_db()
