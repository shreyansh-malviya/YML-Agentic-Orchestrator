"""
Test the argument parser with actual LLM output
"""

import re
import ast

# Simulated LLM output
tool_call_block = '''filesystem.create_file("calculator.py", """
def add(num1, num2):
    return num1 + num2

def main():
    print("Hello")
    
if __name__ == "__main__":
    main()
""")'''

print("Testing parser...")
print("=" * 60)

# Find function call
match = re.search(r'(\w+)\.(\w+)\s*\(', tool_call_block)
if match:
    category = match.group(1)
    function_name = match.group(2)
    args_start = match.end()
    
    print(f"Found: {category}.{function_name}")
    print(f"Args start at position: {args_start}")
    
    # Find matching closing parenthesis
    substring = tool_call_block[args_start:]
    print(f"Substring length: {len(substring)}")
    print(f"First 100 chars: {substring[:100]}")
    
    paren_depth = 1
    in_string = False
    string_char = None
    triple_quote = False
    escape_next = False
    args_end = None
    
    i = 0
    while i < len(substring):
        char = substring[i]
        
        if escape_next:
            escape_next = False
            i += 1
            continue
        
        if char == '\\' and in_string:
            escape_next = True
            i += 1
            continue
        
        # Check for triple quotes
        if i + 2 < len(substring) and substring[i:i+3] in ('"""', "'''"):
            if not in_string:
                in_string = True
                triple_quote = True
                string_char = substring[i:i+3]
                i += 3
                continue
            elif triple_quote and substring[i:i+3] == string_char:
                in_string = False
                triple_quote = False
                string_char = None
                i += 3
                continue
        
        # Check for single/double quotes
        if char in ('"', "'") and not triple_quote:
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
        
        # Count parentheses only when not in string
        if not in_string:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
                if paren_depth == 0:
                    args_end = i
                    break
        
        i += 1
    
    print(f"Args end at position: {args_end}")
    
    if args_end:
        args_str = substring[:args_end]
        print(f"Args string length: {len(args_str)}")
        print(f"Args: {args_str[:200]}...")
        
        # Try to parse
        try:
            eval_str = f"({args_str},)"
            print(f"\\nEval string length: {len(eval_str)}")
            parsed = ast.literal_eval(eval_str)
            print(f"✓ Parsed {len(parsed)} arguments")
            print(f"✓ Arg 1: {parsed[0]}")
            print(f"✓ Arg 2 length: {len(parsed[1])}")
            print(f"✓ Arg 2 preview: {parsed[1][:100]}...")
        except Exception as e:
            print(f"✗ Parse error: {e}")
