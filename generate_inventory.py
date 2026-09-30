import os
import subprocess

def run_git_ls_files():
    result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
    return result.stdout.splitlines()

def categorize_file(path):
    if path.startswith('.backend-venv/'):
        return 'VENDOR/DEPENDENCY', 'Python Virtual Environment', False, 'Skipped as it is a third-party virtual environment'
    if 'node_modules/' in path:
        return 'VENDOR/DEPENDENCY', 'Node Modules', False, 'Skipped node modules'
    if '.next/' in path:
        return 'GENERATED', 'Next.js Build Output', False, 'Skipped generated output'
    if path.endswith(('.png', '.ico', '.jpg', '.jpeg', '.svg', '.gif')):
        return 'BINARY/ASSET', 'Image Asset', False, 'Skipped image asset'
    if path.endswith(('.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin')):
        return 'BINARY/ASSET', 'Compiled Binary', False, 'Skipped compiled binary'
    if path.startswith('mednarrate-admin-desktop/'):
        return 'DESKTOP/TAURI', 'Tauri Desktop App', True, ''
    if path.startswith('mednarrate-admin/'):
        if '__tests__' in path or path.endswith('.test.ts') or path.endswith('.test.tsx'):
            return 'TEST', 'Admin Frontend Test', True, ''
        return 'ADMIN FRONTEND', 'Admin Portal', True, ''
    if path.startswith('mednarrate-backend/'):
        if 'alembic/versions/' in path:
            return 'DATABASE/MIGRATION', 'Database Migration', True, ''
        if 'tests/' in path:
            return 'TEST', 'Backend Test', True, ''
        return 'BACKEND', 'FastAPI Backend', True, ''
    if path.startswith('lib/') or path.startswith('macos/') or path.startswith('ios/') or path.startswith('android/') or path.startswith('linux/') or path.startswith('windows/') or path.startswith('web/') or path == 'pubspec.yaml':
        if path.startswith('test/'):
            return 'TEST', 'Flutter Test', True, ''
        return 'FLUTTER FRONTEND', 'Flutter Mobile/Web/Desktop', True, ''
    if path.startswith('docs/') or path.endswith('.md'):
        return 'DOCUMENTATION', 'Documentation', True, ''
    if path.startswith('.github/') or path == '.gitlab-ci.yml':
        return 'CI/CD', 'CI/CD Configuration', True, ''
    if 'config' in path or path.endswith('.json') or path.endswith('.yaml') or path.endswith('.yml'):
        return 'CONFIGURATION', 'Configuration File', True, ''
    
    return 'UNKNOWN', 'Unknown', True, ''

def main():
    files = run_git_ls_files()
    
    with open('docs/audit/FULL_REPOSITORY_FILE_INVENTORY.md', 'w') as f:
        f.write('# Full Repository File Inventory\n\n')
        f.write('| Path | Category | Purpose | Reviewed? | Reason if Skipped |\n')
        f.write('|---|---|---|---|---|\n')
        
        for path in files:
            category, purpose, reviewed, reason = categorize_file(path)
            f.write(f'| `{path}` | {category} | {purpose} | {"Yes" if reviewed else "No"} | {reason} |\n')

if __name__ == "__main__":
    main()
