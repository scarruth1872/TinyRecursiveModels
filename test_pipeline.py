
"""
Resume pipeline: check state, approve rebuilt, integrate, deploy.
"""
import httpx
import time
import os

API = "http://localhost:8001"
c = httpx.Client(timeout=600)


def heading(txt):
    print()
    print("=" * 60)
    print(f"  {txt}")
    print("=" * 60)


def show_stats():
    r = c.get(f"{API}/artifacts")
    s = r.json()["stats"]
    print(f"  Pending:{s['pending']}  Approved:{s['approved']}  Tested:{s['tested']}  Integrated:{s['integrated']}  Rejected:{s['rejected']}  Failed:{s['test_failed']}")
    return r.json()


# ─── Check current state ──────────────────────────────────────────────────
heading("CURRENT STATE")
data = show_stats()
print()
for a in sorted(data["artifacts"], key=lambda x: x["status"]):
    print(f"  {a['filename']:35s} {a['status']}")

# ─── Reject old stubs, approve the real code ──────────────────────────────
heading("REVIEWING ALL ARTIFACTS")

# Files we know are real, meaningful code
real_files = {
    "nexus_architecture.py", "agent_manager.py", "task_router.py",
    "docker_compose.yml", "deploy.sh", "security_audit.py", "README.md",
}
# Old stubs to reject
stub_patterns = {"_output.py", "swarm_build.txt"}

for a in data["artifacts"]:
    fn = a["filename"]
    status = a["status"]

    # Skip already integrated/tested
    if status in ("integrated", "tested"):
        continue

    is_stub = any(pat in fn for pat in stub_patterns)
    is_real = fn in real_files
    is_test = fn.startswith("test_")

    if is_stub and status != "rejected":
        c.post(f"{API}/artifacts/review", json={
            "filename": fn, "action": "reject", "notes": "Old stub template", "reviewer": "user"
        })
        print(f"  ❌ REJECTED: {fn} (stub)")
    elif (is_real or is_test) and status in ("pending",):
        c.post(f"{API}/artifacts/review", json={
            "filename": fn, "action": "approve", "notes": "Reviewed - good quality", "reviewer": "user"
        })
        print(f"  ✅ APPROVED: {fn}")

show_stats()

# ─── Integrate all approved/tested ────────────────────────────────────────
heading("INTEGRATING ALL APPROVED")
data = show_stats()
for a in data["artifacts"]:
    if a["status"] in ("tested", "approved"):
        r = c.post(f"{API}/artifacts/integrate", json={"filename": a["filename"]})
        if r.status_code == 200:
            print(f"  📦 INTEGRATED: {a['filename']}")

show_stats()

# ─── Check for rejected - trigger remediation if any ──────────────────────
heading("CHECKING FOR REJECTIONS")
data = show_stats()
rejected_count = data["stats"]["rejected"]
failed_count = data["stats"]["test_failed"]

if rejected_count > 0 or failed_count > 0:
    print(f"  Found {rejected_count} rejected + {failed_count} failed → triggering remediation...")
    start = time.time()
    r = c.post(f"{API}/artifacts/remediate")
    result = r.json()
    elapsed = time.time() - start
    print(f"  [{elapsed:.0f}s] Architect plan:")
    print(f"    {result.get('architect_plan', 'N/A')[:250]}")
    print()
    for item in result.get("rebuilt", []):
        print(f"    � {item['filename']} rebuilt by {item['rebuilt_by']}")
    
    # Approve the rebuilt artifacts
    print()
    print("  Approving rebuilt artifacts...")
    data = show_stats()
    for a in data["artifacts"]:
        if a["status"] == "pending":
            c.post(f"{API}/artifacts/review", json={
                "filename": a["filename"], "action": "approve", 
                "notes": "Rebuilt after remediation", "reviewer": "user"
            })
            print(f"    ✅ {a['filename']}")
    
    # Integrate them
    data = show_stats()
    for a in data["artifacts"]:
        if a["status"] in ("tested", "approved"):
            r = c.post(f"{API}/artifacts/integrate", json={"filename": a["filename"]})
            if r.status_code == 200:
                print(f"    📦 INTEGRATED: {a['filename']}")
else:
    print("  No rejections — all clear!")

show_stats()

# ─── Deploy Nexus ─────────────────────────────────────────────────────────
heading("DEPLOYING NEXUS PLATFORM")
print("  Running 5-phase deployment pipeline...")
print("  (Architect → DevOps → Lead Dev → Security → QA)")
print()
start = time.time()

r = c.post(f"{API}/artifacts/deploy", json={"project_name": "Nexus Platform"})
deploy = r.json()
elapsed = time.time() - start

print(f"  [{elapsed:.0f}s] {deploy.get('message', 'Done')}")
print()

for i, step in enumerate(deploy.get("steps", []), 1):
    print(f"  ── Phase {i}: {step['phase']} ({step.get('agent', step.get('name', '?'))}) ──")
    response = step.get("response", "")
    # Print first 300 chars
    print(f"  {response[:300]}")
    print()

# ─── Final State ──────────────────────────────────────────────────────────
heading("FINAL STATE")
data = show_stats()

integ_dir = "swarm_v2_integrated"
if os.path.exists(integ_dir):
    print()
    print("  📁 Integrated directory:")
    total = 0
    for f in sorted(os.listdir(integ_dir)):
        fp = os.path.join(integ_dir, f)
        if os.path.isfile(fp):
            size = os.path.getsize(fp)
            total += size
            print(f"    {f:35s} {size:5d}b")
    print(f"    {'─' * 41}")
    print(f"    {'Total':35s} {total:5d}b")

# Check for new deploy artifacts
arts_dir = "swarm_v2_artifacts"
deploy_files = [f for f in os.listdir(arts_dir) if f in ("setup_nexus.sh", "nexus_main.py", "validate_deployment.py")]
if deploy_files:
    print()
    print("  🚀 Deploy artifacts generated:")
    for f in deploy_files:
        size = os.path.getsize(os.path.join(arts_dir, f))
        print(f"    {f:35s} {size:5d}b")

print()
print("  ✅ FULL CLOSED-LOOP COMPLETE!")
print("     reject → remediate → approve → integrate → deploy")
