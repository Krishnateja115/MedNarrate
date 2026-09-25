import os
import re

for route in ['admins', 'incidents', 'reports', 'support', 'users']:
    filepath = f"src/app/(protected)/{route}/detail/page.tsx"
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r') as f:
        content = f.read()
        
    # 1. Ensure 'use client'; is at the very top.
    content = content.replace("'use client';", "")
    content = content.replace("/* eslint-disable */", "")
    content = "/* eslint-disable */\n'use client';\n" + content
    
    # 2. Fix multiple imports
    # Remove all useSearchParams imports and add exactly one at the top
    content = re.sub(r"import \{ useSearchParams \} from 'next/navigation';\n", "", content)
    content = content.replace("'use client';\n", "'use client';\nimport { useSearchParams } from 'next/navigation';\n")
    
    # Remove multiple useState imports
    content = re.sub(r"import \{ useState \} from 'react';\n", "", content)
    content = content.replace("import { Suspense } from 'react';\n", "import { Suspense, useState } from 'react';\n")
    
    # Clean up empty lines at top
    content = re.sub(r"\n\n\n+", "\n\n", content)

    with open(filepath, 'w') as f:
        f.write(content)
        
    print(f"Fixed {filepath}")
