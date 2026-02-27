#!/usr/bin/env python3
"""
Find all route definitions in app_v2.py to debug the 404 issue.
"""

import re

with open('swarm_v2/app_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all @app.get, @app.post, etc.
pattern = r'@app\.(get|post|put|delete|patch|head|options)\(([^)]+)\)'
matches = re.findall(pattern, content)

print("Found route definitions:")
for i, (method, path) in enumerate(matches):
    print(f"{i+1:3}. @app.{method}({path})")

# Look specifically for /artifacts/stats
print("\n=== Looking for /artifacts/stats ===")
for line_num, line in enumerate(content.split('\n'), 1):
    if '/artifacts/stats' in line:
        print(f"Line {line_num}: {line.strip()}")
        # Show context
        start = max(0, line_num - 3)
        end = line_num + 3
        lines = content.split('\n')
        for ctx_line in range(start, min(end, len(lines))):
            print(f"  {ctx_line+1:4}: {lines[ctx_line].rstrip()}")

# Check for duplicate function definitions
print("\n=== Checking for duplicate function definitions ===")
func_pattern = r'async def artifact_stats'
for line_num, line in enumerate(content.split('\n'), 1):
    if 'artifact_stats' in line:
        print(f"Line {line_num}: {line.strip()}")

# Also check for any middleware that might be interfering
print("\n=== Checking for middleware registration ===")
for line_num, line in enumerate(content.split('\n'), 1):
    if 'add_middleware' in line:
        print(f"Line {line_num}: {line.strip()}")