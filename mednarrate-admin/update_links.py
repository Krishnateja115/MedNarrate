import os
import re

directories_to_scan = ['src/app', 'src/components']
routes_to_fix = ['users', 'reports', 'support', 'incidents', 'admins']

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # We are looking for things like: `/users/${something}`
    # and we want to replace with `/users/detail?id=${something}`
    # Also we might have router.push(`/users/${something}`)
    
    for route in routes_to_fix:
        # Regex to find: /route/${var}
        # Be careful not to replace /route/detail?id=${var} if already there
        pattern = rf'/{route}/\${{([^}]+)}}'
        replacement = rf'/{route}/detail?id=${{\1}}'
        content = re.sub(pattern, replacement, content)
        
        # Also handle regular string concatenation if any: '/users/' + something
        pattern2 = rf"/{route}/' \+ ([a-zA-Z0-9_\.]+)"
        replacement2 = rf"/{route}/detail?id=' + \1"
        content = re.sub(pattern2, replacement2, content)
        
        # Also handle Next.js static links if any, e.g., href="/users/123"
        # Not safe to blindly replace string literals, but we know it's a dynamic app.
        
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {filepath}")

for d in directories_to_scan:
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith('.tsx') or file.endswith('.ts'):
                process_file(os.path.join(root, file))
