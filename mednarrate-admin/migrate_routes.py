import os
import glob
import shutil

# Find all [id] directories
dynamic_dirs = glob.glob('src/app/**/\[id\]', recursive=True)

print(f"Found dynamic dirs: {dynamic_dirs}")

for dir_path in dynamic_dirs:
    # We want to rename [id] to detail
    new_dir_path = dir_path.replace('[id]', 'detail')
    
    # 1. Rename directory
    print(f"Renaming {dir_path} to {new_dir_path}")
    os.rename(dir_path, new_dir_path)
    
    # 2. We need to merge ClientPage.tsx into page.tsx or just modify ClientPage.tsx and page.tsx
    # Actually it's easier to just take ClientPage.tsx, modify it to use useSearchParams, and overwrite page.tsx
    client_page_path = os.path.join(new_dir_path, 'ClientPage.tsx')
    page_path = os.path.join(new_dir_path, 'page.tsx')
    
    if os.path.exists(client_page_path):
        with open(client_page_path, 'r') as f:
            content = f.read()
        
        # Modify content to use useSearchParams
        # Replace: export default function UserDetailPage({ params }: { params: Promise<{ id: string }> }) {
        # With:
        # import { useSearchParams } from 'next/navigation';
        # export default function DetailPage() {
        #   const searchParams = useSearchParams();
        #   const itemId = searchParams.get('id');
        #
        # Remove: const resolvedParams = use(params);
        # Remove: const userId = resolvedParams.id; (or replace with itemId logic)
        
        # Using a simpler string replacement:
        content = content.replace("import { use, useState }", "import { useState }")
        content = content.replace("import { use, useEffect", "import { useEffect")
        content = content.replace("import { use }", "")
        if "useSearchParams" not in content:
            content = content.replace("import { useState", "import { useSearchParams } from 'next/navigation';\nimport { useState")
            content = content.replace("import { useQuery", "import { useSearchParams } from 'next/navigation';\nimport { useQuery")
        
        import re
        
        # Replace the component signature
        content = re.sub(
            r'export default function [A-Za-z0-9_]+\(\{ params \}.*?\) \{',
            'export default function DetailPage() {\n  const searchParams = useSearchParams();\n  const extractedId = searchParams.get(\'id\');',
            content,
            flags=re.DOTALL
        )
        
        # Replace use(params)
        content = re.sub(r'const [a-zA-Z0-9_]+ = use\(params\);', '', content)
        
        # Replace whateverId = resolvedParams.id with whateverId = extractedId;
        content = re.sub(r'const ([a-zA-Z0-9_]+Id) = [a-zA-Z0-9_]+\.id;', r'const \1 = extractedId;', content)
        
        # If there's no id, we should show a not found or handle it gracefully
        # Let's wrap the return with a check
        content = content.replace('const queryClient = useQueryClient();', 'const queryClient = useQueryClient();\n  if (!extractedId) return <div className="p-8">No ID provided</div>;')
        
        # Now we need to wrap the whole thing in Suspense for static export compatibility
        final_content = "import { Suspense } from 'react';\n" + content
        final_content = final_content.replace('export default function DetailPage', 'function DetailContent')
        final_content += "\n\nexport default function Page() {\n  return (\n    <Suspense fallback={<div className=\"p-8\">Loading...</div>}>\n      <DetailContent />\n    </Suspense>\n  );\n}\n"
        
        with open(page_path, 'w') as f:
            f.write(final_content)
        
        os.remove(client_page_path)
