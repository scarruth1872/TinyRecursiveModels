# Swarm OS: Nexus Launch Protocol (Recursive Boot v1.0)
# This script ensures a clean, sequential, and verified startup of all Swarm services.

Write-Host "--- INITIALIZING NEURAL BRIDGE BOOT SEQUENCE ---" -ForegroundColor Cyan

# 1. Process Cleanup (Ensures no port conflicts or stale logic)
Write-Host "[1/5] Purging stale neural threads (Node/Python)..." -ForegroundColor Yellow
Stop-Process -Name node, python -ErrorAction SilentlyContinue -Force
Start-Sleep -Seconds 2

# 2. Environment Configuration
Write-Host "[2/5] Calibrating Environment Variables..." -ForegroundColor Yellow
$env:PYTHONPATH = "f:\Development sites\TRM agent swarm"
$env:OLLAMA_VULKAN = "1"
$env:OLLAMA_NUM_PARALLEL = "2"
$env:OLLAMA_MAX_LOADED_MODELS = "2"

# 3. Core API Boot (Sequential dependency)
Write-Host "[3/5] Powering up Brain API (app_v2.py)..." -ForegroundColor Green
$backendCmd = "& '.\venv\Scripts\Activate.ps1'; python 'f:\Development sites\TRM agent swarm\swarm_v2\app_v2.py'"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -NoNewWindow

# Wait for Brain Initialization
Write-Host "Waiting for Brain to heat up (10s)..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# 4. MCP Tool Synthesis Boot
Write-Host "[4/5] Activating Synthesized MCP Tools..." -ForegroundColor Green
$toolsCmd = "& '.\venv\Scripts\Activate.ps1'; python 'f:\Development sites\TRM agent swarm\start_tools.py'"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $toolsCmd -NoNewWindow

# Wait for Tool Verification
Start-Sleep -Seconds 8

# 5. Neural Bridge Dashboard Boot
Write-Host "[5/5] Bridging to Frontend Dashboard..." -ForegroundColor Cyan
Set-Location "f:\Development sites\TRM agent swarm\dashboard"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev" -NoNewWindow

Write-Host "--- BOOT SEQUENCE COMPLETE ---" -ForegroundColor Cyan
Write-Host "Dashboard: http://localhost:5173" -ForegroundColor Green
Write-Host "Backend API: http://localhost:8001" -ForegroundColor Green
Write-Host "Neural Pipeline: ACTIVE" -ForegroundColor Green
