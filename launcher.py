
import os
import sys
import subprocess
import time

# Set PYTHONPATH to current directory
os.environ["PYTHONPATH"] = os.getcwd()
os.environ["OLLAMA_VULKAN"] = "1"

print(f"Current directory: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ['PYTHONPATH']}")

# Start tools
print("Starting tools via start_tools.py...")
try:
    subprocess.Popen([sys.executable, "start_tools.py"])
except Exception as e:
    print(f"Failed to start tools: {e}")

# Start OpenClaw Gateway (Perception Layer)
print("Starting OpenClaw Gateway...")
try:
    subprocess.Popen([sys.executable, "swarm_v2/core/openclaw_gateway.py"])
except Exception as e:
    print(f"Failed to start OpenClaw: {e}")

# Wait a bit for tools
time.sleep(5)

# Start API
print("Starting API via swarm_v2/app_v2.py...")
try:
    # Use the same python executable
    # Note: We run this in the background or just keep this script running?
    # Better to use Popen so this script can finish or monitor.
    proc = subprocess.Popen([sys.executable, "swarm_v2/app_v2.py"])
    print(f"API process started with PID {proc.pid}")
    
    # Keep alive to see if it stays up
    while True:
        if proc.poll() is not None:
            print(f"API process exited with code {proc.returncode}")
            break
        time.sleep(1)
except Exception as e:
    print(f"Failed to start API: {e}")
