import httpx
import json

def batch_maintenance():
    api_base = "http://127.0.0.1:8001"
    
    print("--- Swarm Maintenance: Batch Verification & Integration ---")
    
    # 1. Fetch all artifacts
    resp = httpx.get(f"{api_base}/artifacts?grouped=true")
    if resp.status_code != 200:
        print("Error fetching artifacts")
        return
        
    groups = resp.json().get("groups", {})
    approved = groups.get("approved", [])
    
    # Identify files to verify (security) and integrate
    to_verify = [a["filename"] for a in approved if a.get("security_status") == "pending_scan"]
    to_integrate = [a["filename"] for a in approved] # User wants to batch integrate approved ones
    
    if to_verify:
        print(f"Verifying {len(to_verify)} artifacts...")
        httpx.post(f"{api_base}/artifacts/security-verify", json=to_verify)
    
    if to_integrate:
        print(f"Integrating {len(to_integrate)} artifacts...")
        int_resp = httpx.post(f"{api_base}/artifacts/batch-integrate", json={
            "filenames": to_integrate,
            "target_subdir": "integrated_batch"
        })
        print(f"Integration Result: {int_resp.status_code}")
        # print(int_resp.json())

    print("\nRefreshing Artifact Matrix...")
    stats = httpx.get(f"{api_base}/artifacts").json().get("stats", {})
    print(f"Total Integrated: {stats.get('integrated', 0)}")
    print(f"Pending Review: {stats.get('pending', 0)}")

if __name__ == "__main__":
    batch_maintenance()
