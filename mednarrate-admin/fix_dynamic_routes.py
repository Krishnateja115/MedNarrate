import os
import glob

files = glob.glob('src/app/**/\[id\]/page.tsx', recursive=True)

for file in files:
    with open(file, 'r') as f:
        content = f.read()
    
    if 'export function generateStaticParams' in content:
        continue
        
    client_comp_path = file.replace('page.tsx', 'ClientPage.tsx')
    with open(client_comp_path, 'w') as f:
        f.write(content)
    
    server_comp_content = """import ClientPage from './ClientPage';

export function generateStaticParams() {
  return []; // We generate no static paths at build time, but we need this for output: export
}

export default function Page(props: any) {
  return <ClientPage {...props} />;
}
"""
    with open(file, 'w') as f:
        f.write(server_comp_content)
