import os
import re
import json

arb_path = 'lib/l10n/app_en.arb'
with open(arb_path, 'r') as f:
    arb_data = json.load(f)

# Extract mappings of string -> key
str_to_key = {}
for k, v in arb_data.items():
    if not k.startswith('@') and k != '@@locale':
        # Escape quotes and other regex special chars if any, but they are mostly simple strings
        str_to_key[v] = k

def get_dart_files(directory):
    dart_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.dart'):
                dart_files.append(os.path.join(root, file))
    return dart_files

dart_files = get_dart_files('lib/features') + get_dart_files('lib/shared/widgets') + ['lib/main.dart']

import_statement = "import 'package:flutter_gen/gen_l10n/app_localizations.dart';\n"

# We sort by length descending to replace longer strings first (avoid partial matches)
sorted_strings = sorted(str_to_key.keys(), key=len, reverse=True)

# Edge case: "Reports" can be a tab, title, etc. Same for "Dashboard", "Settings", etc.
for file in dart_files:
    with open(file, 'r') as f:
        content = f.read()

    original_content = content
    modified = False

    for s in sorted_strings:
        key = str_to_key[s]
        
        # Replace Text('string') or Text("string")
        pattern_text = r"Text\s*\(\s*['\"]" + re.escape(s) + r"['\"]\s*([,)])"
        repl_text = r"Text(AppLocalizations.of(context)!." + key + r"\1"
        if re.search(pattern_text, content):
            content = re.sub(pattern_text, repl_text, content)
            modified = True

        # Replace 'string' or "string" in other common places (e.g. label:, title:, etc)
        # Be careful not to replace things like routes or map keys. 
        # We look for explicit UI prefixes or just generally where it's passed as a parameter.
        # This regex matches common named parameters or list items.
        pattern_param = r"((?:label|title|text|hintText|tooltip|message)\s*:\s*)['\"]" + re.escape(s) + r"['\"]"
        repl_param = r"\1AppLocalizations.of(context)!." + key
        if re.search(pattern_param, content):
            content = re.sub(pattern_param, repl_param, content)
            modified = True
            
        # Replace strings in lists or positional args (like Helpers.showSuccess(context, 'Success'))
        # This is a bit tricky, but we can target Helpers.showSuccess and showError specifically
        pattern_helper = r"(Helpers\.show(?:Success|Error)\(context,\s*)['\"]" + re.escape(s) + r"['\"]"
        repl_helper = r"\1AppLocalizations.of(context)!." + key
        if re.search(pattern_helper, content):
            content = re.sub(pattern_helper, repl_helper, content)
            modified = True
            
        # BottomNavigationBarItem label
        pattern_bottom_nav = r"(BottomNavigationBarItem\s*\([^)]*label\s*:\s*)['\"]" + re.escape(s) + r"['\"]"
        repl_bottom_nav = r"\1AppLocalizations.of(context)!." + key
        if re.search(pattern_bottom_nav, content):
            content = re.sub(pattern_bottom_nav, repl_bottom_nav, content)
            modified = True

        # QuickActionCard title
        pattern_quick = r"(QuickActionCard\s*\([^)]*title\s*:\s*)['\"]" + re.escape(s) + r"['\"]"
        repl_quick = r"\1AppLocalizations.of(context)!." + key
        if re.search(pattern_quick, content):
            content = re.sub(pattern_quick, repl_quick, content)
            modified = True

        # DashboardStatisticsCard title
        pattern_stat = r"(DashboardStatisticsCard\s*\([^)]*title\s*:\s*)['\"]" + re.escape(s) + r"['\"]"
        repl_stat = r"\1AppLocalizations.of(context)!." + key
        if re.search(pattern_stat, content):
            content = re.sub(pattern_stat, repl_stat, content)
            modified = True

    if modified:
        # Add import if missing
        if "package:flutter_gen/gen_l10n/app_localizations.dart" not in content:
            # find last import
            last_import_idx = content.rfind("import '")
            if last_import_idx != -1:
                end_of_line = content.find('\n', last_import_idx)
                content = content[:end_of_line+1] + import_statement + content[end_of_line+1:]
            else:
                content = import_statement + content
                
        with open(file, 'w') as f:
            f.write(content)
        print(f"Updated {file}")

