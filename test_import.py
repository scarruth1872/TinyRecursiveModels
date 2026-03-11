import sys
import traceback

sys.path.append(".")

try:
    import swarm_v2.app_v2
    print("SUCCESS")
except Exception as e:
    print("FAILED")
    traceback.print_exc()
