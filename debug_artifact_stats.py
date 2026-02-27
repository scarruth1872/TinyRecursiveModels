#!/usr/bin/env python3
"""
Debug the artifact_stats endpoint by examining the exact code.
"""

with open('swarm_v2/app_v2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find artifact_stats function and surrounding context
print("=== Examining artifact_stats function ===")
for i, line in enumerate(lines):
    if '@app.get("/artifacts/stats")' in line or 'async def artifact_stats' in line:
        print(f"Line {i+1}: {line.rstrip()}")
        
        # Show more context
        start = max(0, i-10)
        end = min(len(lines), i+20)
        print(f"\nContext (lines {start+1} to {end}):")
        for j in range(start, end):
            prefix = ">>> " if j == i else "    "
            print(f"{prefix}{j+1:4}: {lines[j].rstrip()}")

# Check for syntax errors in the file
print("\n=== Checking for potential syntax errors ===")
# Look for any unmatched quotes, brackets, etc.
for i, line in enumerate(lines):
    # Check for obvious syntax issues
    if line.count('(') != line.count(')'):
        print(f"Line {i+1}: Mismatched parentheses - {line.rstrip()}")
    if line.count('[') != line.count(']'):
        print(f"Line {i+1}: Mismatched brackets - {line.rstrip()}")
    if line.count('{') != line.count('}'):
        print(f"Line {i+1}: Mismatched braces - {line.rstrip()}")

# Check if there's a duplicate route with the same path
print("\n=== Checking for duplicate /artifacts/stats routes ===")
artifact_stats_count = 0
for i, line in enumerate(lines):
    if '@app.get("/artifacts/stats")' in line:
        artifact_stats_count += 1
        print(f"Found at line {i+1}: {line.rstrip()}")

if artifact_stats_count > 1:
    print(f"WARNING: Found {artifact_stats_count} definitions of /artifacts/stats")
elif artifact_stats_count == 1:
    print("Found exactly one /artifacts/stats route definition")
else:
    print("ERROR: No /artifacts/stats route definition found!")

# Check the actual FastAPI app variable name
print("\n=== Checking FastAPI app variable ===")
for i, line in enumerate(lines):
    if 'app = FastAPI' in line:
        print(f"Line {i+1}: {line.rstrip()}")
        # Show what variable name is used
        if 'app' in line:
            print("  Using 'app' as the FastAPI instance variable")

# Check if there are any other FastAPI instances
print("\n=== Checking for other FastAPI instances ===")
for i, line in enumerate(lines):
    if 'FastAPI(' in line and 'app = FastAPI' not in line:
        print(f"Line {i+1}: {line.rstrip()}")