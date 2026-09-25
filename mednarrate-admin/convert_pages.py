import os
import re

dirs = [
    'src/app/(protected)/admins/detail',
    'src/app/(protected)/incidents/detail',
    'src/app/(protected)/reports/detail',
    'src/app/(protected)/support/detail',
    'src/app/(protected)/users/detail',
]

for dir_path in dirs:
    client_page_path = os.path.join(dir_path, 'ClientPage.tsx')
    page_path = os.path.join(dir_path, 'page.tsx')
    
    if os.path.exists(client_page_path):
        with open(client_page_path, 'r') as f:
            content = f.read()
        
        # Add useSearchParams
        content = content.replace("import { use, useState }", "import { useState }")
        content = content.replace("import { use, useEffect", "import { useEffect")
        content = content.replace("import { use }", "")
        if "useSearchParams" not in content:
            content = content.replace("import { useState", "import { useSearchParams } from 'next/navigation';\nimport { useState")
            content = content.replace("import { useQuery", "import { useSearchParams } from 'next/navigation';\nimport { useQuery")
        
        # Replace the component signature
        content = re.sub(
            r'export default function ([A-Za-z0-9_]+)\(\{ params \}.*?\) \{',
            r'function \1Content() {\n  const searchParams = useSearchParams();\n  const extractedId = searchParams.get(\'id\');',
            content,
            flags=re.DOTALL
        )
        
        # Find the function name we just captured to use in the Suspense wrapper
        match = re.search(r'function ([A-Za-z0-9_]+Content)\(\) \{', content)
        func_name = match.group(1) if match else "DetailContent"
        
        # Remove use(params)
        content = re.sub(r'const [a-zA-Z0-9_]+ = use\(params\);', '', content)
        
        # Replace variable assignment
        content = re.sub(r'const ([a-zA-Z0-9_]+Id) = [a-zA-Z0-9_]+\.id;', r'const \1 = extractedId;', content)
        
        # Some files might just use `resolvedParams.id` directly if they didn't destruct
        content = content.replace("resolvedParams.id", "extractedId")
        
        # Add early return for missing ID
        content = content.replace('const queryClient = useQueryClient();', 'const queryClient = useQueryClient();\n  if (!extractedId) return <div className="p-8">No ID provided</div>;')
        
        # In case the component didn't have useQueryClient
        if "if (!extractedId)" not in content:
            # just put it after extractedId assignment
            content = content.replace("const extractedId = searchParams.get('id');", "const extractedId = searchParams.get('id');\n  if (!extractedId) return <div className=\"p-8 text-center text-muted-foreground\">No ID provided</div>;")
            
        final_content = "import { Suspense } from 'react';\n" + content
        final_content += f"\n\nexport default function Page() {{\n  return (\n    <Suspense fallback={{<div className=\"p-8\">Loading...</div>}}>\n      <{func_name} />\n    </Suspense>\n  );\n}}\n"
        
        with open(page_path, 'w') as f:
            f.write(final_content)
            
        os.remove(client_page_path)
