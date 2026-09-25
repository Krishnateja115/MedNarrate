#!/bin/bash

# Target replacements
# For pattern: href={`/route/${variable}`} -> href={`/route/detail?id=${variable}`}
# Or href={`/route/${variable.id}`} -> href={`/route/detail?id=${variable.id}`}

routes=("admins" "support" "users" "incidents" "reports")

for route in "${routes[@]}"; do
  # Find files containing the route pattern and replace it inline
  find src/app -type f -name "*.tsx" -exec sed -i '' -e "s|href={\`/\\(${route}\\)/\\$|href={\`/\\1/detail?id=\\$|g" {} +
done

# Also there's one edge case in support/detail/page.tsx:
# href={`/reports/${ticket.related_report_id}`} 
# The above regex will catch it because it replaces /reports/${ with /reports/detail?id=${
