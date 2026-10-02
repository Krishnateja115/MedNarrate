import os
import re
import ast

def parse_file(path):
    with open(path) as f:
        tree = ast.parse(f.read())
    
    results = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            route_info = None
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    if dec.func.value.id in ('router', 'app'):
                        method = dec.func.attr.upper()
                        path_arg = dec.args[0].value if dec.args else ""
                        route_info = {"method": method, "path": path_arg, "deps": []}
            if route_info:
                # Find Depends() in arguments
                for arg in node.args.args + node.args.kwonlyargs:
                    if arg.arg == "admin_ctx":
                        # this is usually where require_permission is used
                        pass
                
                # Simple regex parsing for dependency
                # We can just grep the source of the function
                source = ast.get_source_segment(open(path).read(), node)
                import re
                deps = re.findall(r'Depends\((.*?)\)', source)
                route_info['deps'] = deps
                results.append(route_info)
    return results

import glob
for file in glob.glob("app/api/v1/admin_*.py"):
    res = parse_file(file)
    for r in res:
        print(f"| {file.split('/')[-1]} | {r['method']} | {r['path']} | {r['deps']} |")
