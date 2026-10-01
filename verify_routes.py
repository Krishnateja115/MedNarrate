import os
import ast
import re

FRONTEND_DIR = "mednarrate-admin/src/app"
BACKEND_DIR = "mednarrate-backend/app/api/v1"

frontend_routes = []
backend_endpoints = []

def extract_fetch_calls(filepath):
    calls = []
    with open(filepath, 'r') as f:
        content = f.read()
        
    # Find all fetchApi('/api/v1/...') or fetch('/api/v1/...')
    matches = re.finditer(r'(fetchApi|fetch)\s*\(\s*[\'"`](/api/v1/[^\'"`]+)[\'"`]', content)
    for m in matches:
        calls.append(m.group(2))
    return calls

for root, dirs, files in os.walk(FRONTEND_DIR):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.ts'):
            filepath = os.path.join(root, f)
            rel_path = os.path.relpath(filepath, FRONTEND_DIR)
            calls = extract_fetch_calls(filepath)
            
            # Simple heuristic for permission, e.g. `<RequirePermission permission="dashboard.view">`
            with open(filepath, 'r') as file_obj:
                content = file_obj.read()
                perms = re.findall(r'permission=[\'"]([^\'"]+)[\'"]', content)
                # also check for requirePermission in getServerSession or similar
                perms += re.findall(r'requirePermission\([\'"]([^\'"]+)[\'"]\)', content)
            
            frontend_routes.append({
                "file": rel_path,
                "calls": calls,
                "permissions": list(set(perms))
            })

def parse_fastapi_router(filepath):
    endpoints = []
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                            # Extract path
                            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                path = decorator.args[0].value
                                
                                # Find Depends(require_permission('...'))
                                perms = []
                                for arg in node.args.defaults:
                                    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == 'Depends':
                                        if isinstance(arg.args[0], ast.Call) and isinstance(arg.args[0].func, ast.Name):
                                            if arg.args[0].func.id in ['require_permission', 'require_any_permission', 'require_all_permissions']:
                                                if isinstance(arg.args[0].args[0], ast.Constant):
                                                    perms.append(arg.args[0].args[0].value)
                                                elif isinstance(arg.args[0].args[0], ast.List):
                                                    for elt in arg.args[0].args[0].elts:
                                                        if isinstance(elt, ast.Constant):
                                                            perms.append(elt.value)
                                                            
                                endpoints.append({
                                    "method": decorator.func.attr.upper(),
                                    "path": path,
                                    "function": node.name,
                                    "permissions": perms
                                })
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        
    return endpoints

for root, dirs, files in os.walk(BACKEND_DIR):
    for f in files:
        if f.endswith('.py') and not f.startswith('__'):
            filepath = os.path.join(root, f)
            rel_path = os.path.relpath(filepath, BACKEND_DIR)
            endpoints = parse_fastapi_router(filepath)
            if endpoints:
                backend_endpoints.append({
                    "file": rel_path,
                    "endpoints": endpoints
                })

print("--- FRONTEND ROUTES ---")
for r in frontend_routes:
    if r['calls'] or r['permissions']:
        print(f"File: {r['file']}")
        if r['permissions']:
            print(f"  Permissions: {r['permissions']}")
        if r['calls']:
            print(f"  API Calls: {r['calls']}")

print("\n--- BACKEND ENDPOINTS ---")
for b in backend_endpoints:
    print(f"\nFile: {b['file']}")
    for e in b['endpoints']:
        print(f"  {e['method']} {e['path']} -> {e['permissions']}")
