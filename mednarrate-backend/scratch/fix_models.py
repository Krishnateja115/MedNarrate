import os
import re
import glob

models_dir = "/Users/harsha/Downloads/Sem 5/NLP/mednarrate/mednarrate-backend/app/models"

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # 1. Replace PickleType with JSON
    content = content.replace("PickleType", "JSON")
    # If JSON is not imported but PickleType was, it might just work if we add it or replace it.
    if "PickleType" in original and "JSON" not in content[:content.find("class ")]:
        content = re.sub(r'(from sqlalchemy .*?)(PickleType)(.*?)', r'\1JSON\3', content)

    # 2. Replace sqlite_autoincrement=True
    content = content.replace("sqlite_autoincrement=True", "autoincrement=True")

    # 3. Ensure DateTime(timezone=True)
    # Match Column(DateTime, ...) or Column(DateTime(), ...) and replace with DateTime(timezone=True)
    content = re.sub(r'DateTime(?!\(timezone=True\))(?:\(\))?', 'DateTime(timezone=True)', content)

    # 4. Ensure Text for large content (e.g., replace String(2000) or similar with Text)
    # The prompt says: "Ensure all Text columns that store medical report content use Text (not String with length limits)"
    # We will look for String(length) and replace with Text in specific places or just replace `String(...)` with `Text` for specific column names like 'content', 'original_text', etc.
    # To be safe, I'll just change String(>255) to Text.
    content = re.sub(r'String\(\d{3,}\)', 'Text', content)
    # Also if there's any String() for report content it should be Text.
    # Let's import Text if not imported
    if 'Text' in content and 'Text' not in original[:original.find("class ")] and 'Text' not in content[:content.find("class ")]:
        # crude but effective
        content = content.replace('from sqlalchemy import ', 'from sqlalchemy import Text, ')

    if original != content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {filepath}")

for f in glob.glob(os.path.join(models_dir, "*.py")):
    process_file(f)
