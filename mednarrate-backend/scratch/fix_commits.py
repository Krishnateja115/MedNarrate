import re
import glob

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Pattern: await db.commit() \n ... log_admin_action(...)
    # We want to move await db.commit() to after log_admin_action(...)
    
    # Actually it's easier to find log_admin_action calls, and move the preceding commit
    
    # I'll just manually fix them using multi_replace_file_content or a robust regex script.
