#!/usr/bin/env python3
"""
Inspect FastAPI routes to see if /artifacts/stats is registered.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import the FastAPI app from swarm_v2/app_v2.py
print("=== Importing app_v2 module ===")
try:
    # We need to import the app variable
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_v2", "swarm_v2/app_v2.py")
    module = importlib.util.module_from_spec(spec)
    
    # We need to mock some dependencies that might fail
    import fastapi
    from fastapi import FastAPI
    
    # Mock the missing imports
    class Mock:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return self
        def __getattr__(self, name):
            return Mock()
    
    # Create mock objects for imports that might fail
    sys.modules['swarm_v2.experts.registry'] = Mock()
    sys.modules['swarm_v2.core.artifact_pipeline'] = Mock()
    sys.modules['swarm_v2.skills.learning_engine'] = Mock()
    sys.modules['swarm_v2.mcp.synthesizer'] = Mock()
    sys.modules['swarm_v2.core.agent_mesh'] = Mock()
    sys.modules['swarm_v2.core.global_memory'] = Mock()
    sys.modules['swarm_v2.core.monitor_daemon'] = Mock()
    sys.modules['swarm_v2.core.remediation_engine'] = Mock()
    sys.modules['swarm_v2.core.resource_arbiter'] = Mock()
    sys.modules['swarm_v2.core.expert_registry'] = Mock()
    sys.modules['swarm_v2.core.task_arbiter'] = Mock()
    sys.modules['swarm_v2.core.federation'] = Mock()
    sys.modules['swarm_v2.core.reconnaissance_daemon'] = Mock()
    sys.modules['swarm_v2.core.chain_of_verification'] = Mock()
    sys.modules['swarm_v2.core.neural_wall'] = Mock()
    sys.modules['swarm_v2.core.self_healing_infra'] = Mock()
    sys.modules['swarm_v2.core.zero_human_test_gen'] = Mock()
    sys.modules['swarm_v2.core.auto_changelog'] = Mock()
    sys.modules['swarm_v2.core.mcp_tool_evolver'] = Mock()
    sys.modules['swarm_v2.core.swarm_performance_insights'] = Mock()
    sys.modules['swarm_v2.core.deterministic_forge'] = Mock()
    sys.modules['swarm_v2.core.telemetry'] = Mock()
    sys.modules['swarm_v2.core.proactive_loop'] = Mock()
    sys.modules['swarm_v2.core.sentinel'] = Mock()
    sys.modules['swarm_v2.core.redis_mock'] = Mock()
    
    # Mock psutil
    sys.modules['psutil'] = Mock()
    
    # Try to execute the module
    spec.loader.exec_module(module)
    
    # Get the app variable
    app = module.app
    print(f"Successfully imported app: {app}")
    
    # Inspect routes
    print("\n=== Inspecting routes ===")
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"Path: {route.path}, Methods: {getattr(route, 'methods', 'N/A')}")
            if route.path == "/artifacts/stats":
                print(f"  FOUND /artifacts/stats!")
                print(f"  Endpoint: {route.endpoint}")
                print(f"  Name: {route.name}")
    
    # Count routes with /artifacts/stats
    artifact_stats_routes = [r for r in app.routes if hasattr(r, 'path') and r.path == "/artifacts/stats"]
    print(f"\nTotal /artifacts/stats routes found: {len(artifact_stats_routes)}")
    
    # Also check for similar paths
    print("\n=== Checking for similar artifact paths ===")
    artifact_paths = [r for r in app.routes if hasattr(r, 'path') and '/artifact' in r.path]
    for route in artifact_paths:
        print(f"Path: {route.path}, Methods: {getattr(route, 'methods', 'N/A')}")
    
except Exception as e:
    print(f"Error importing/inspecting: {e}")
    import traceback
    traceback.print_exc()

# Alternative: parse the file to check syntax
print("\n=== Checking file syntax ===")
try:
    with open('swarm_v2/app_v2.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to compile it
    compile(content, 'swarm_v2/app_v2.py', 'exec')
    print("File compiles successfully (no syntax errors)")
except SyntaxError as e:
    print(f"Syntax error: {e}")
    print(f"Line {e.lineno}, offset {e.offset}")
    # Show the problematic line
    lines = content.split('\n')
    if e.lineno - 1 < len(lines):
        print(f"Problematic line: {lines[e.lineno - 1]}")