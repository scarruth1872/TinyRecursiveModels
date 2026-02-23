
# Swarm V2: Targeted GPU Enablement (Navi 22 Safe Mode)
# This script tries to enable GPU offloading for RX 6700 XT with minimal pressure

Write-Host "--- Ollama Targeted GPU Enablement ---" -ForegroundColor Cyan

# 1. Set environment variables (Scoped to process first)
Write-Host "[1/3] Setting RX 6700 XT Overrides..." -ForegroundColor Yellow
# HSA_OVERRIDE_GFX_VERSION=10.3.0 is the standard for Navi 22
$env:HSA_OVERRIDE_GFX_VERSION = "10.3.0"
# Disable parallel streams for now to verify single-agent GPU stability
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_MAX_LOADED_MODELS = "1"

# 2. Restart Ollama
Write-Host "[2/3] Restarting Ollama with DEBUG tracing..." -ForegroundColor Yellow
Get-Process -Name ollama* -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
$env:OLLAMA_DEBUG = "1"
# We'll pipe output to a file to check for ROCm initialization errors
Start-Process "ollama" -ArgumentList "serve" -NoNewWindow -RedirectStandardOutput "gpu_discovery.log"
Start-Sleep -Seconds 5

# 3. Test a small model and check if it hits GPU
Write-Host "[3/3] Running GPU Test (deepseek-r1:1.5b)..." -ForegroundColor Yellow
ollama run deepseek-r1:1.5b "say 'GPU Active'" --verbose

Write-Host "`nChecking Ollama Status:" -ForegroundColor Cyan
ollama ps

Write-Host "`nIf you see 'GPU' under PROCESSOR above, the fix worked!" -ForegroundColor Green
Write-Host "If not, check 'gpu_discovery.log' for 'amdgpu' or 'rocm' errors."
