import re
import sys

def rewrite_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # We will find `await log_admin_action(`
    # and then find the matching closing `)`
    
    idx = 0
    while True:
        idx = content.find("await log_admin_action(", idx)
        if idx == -1:
            break
            
        start = idx + len("await log_admin_action(")
        paren_count = 1
        end = start
        while end < len(content) and paren_count > 0:
            if content[end] == '(':
                paren_count += 1
            elif content[end] == ')':
                paren_count -= 1
            end += 1
            
        args_str = content[start:end-1]
        
        # Split args_str by comma but respect brackets/braces/quotes
        args = []
        current_arg = ""
        in_quote = False
        quote_char = None
        bracket_count = 0
        brace_count = 0
        
        for char in args_str:
            if char == '"' or char == "'":
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif char == quote_char:
                    in_quote = False
                current_arg += char
            elif not in_quote:
                if char == '[': bracket_count += 1
                elif char == ']': bracket_count -= 1
                elif char == '{': brace_count += 1
                elif char == '}': brace_count -= 1
                elif char == ',' and bracket_count == 0 and brace_count == 0:
                    args.append(current_arg.strip())
                    current_arg = ""
                    continue
                current_arg += char
            else:
                current_arg += char
        if current_arg.strip():
            args.append(current_arg.strip())
            
        if len(args) >= 7 and "actor_admin_id" not in args_str:
            db = args[0]
            admin_ctx = args[1]
            action = args[2]
            resource_type = args[3]
            resource_id = args[4]
            metadata = args[5]
            request = args[6]
            
            new_call = f"""await log_admin_action(
        db={db},
        action={action},
        actor_admin_id={admin_ctx}.user_id,
        resource_type={resource_type},
        resource_id={resource_id},
        metadata={metadata},
        request={request}
    )
    await db.commit()"""
            
            content = content[:idx] + new_call + content[end:]
            idx = idx + len(new_call)
        else:
            idx = end

    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    rewrite_file("app/api/v1/admin_users.py")
