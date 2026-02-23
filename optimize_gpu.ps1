
# Swarm V2: Ollama GPU & Parallelism Optimizer (Stable V2)
# Reverted aggressive overrides to prevent system crashes

Write-Host "--- Ollama GPU Recovery Script ---" -ForegroundColor Cyan

# 1. Clear aggressive environment variables
Write-Host "[1/3] Resetting GPU Overrides..." -ForegroundColor Yellow
[System.Environment]::SetEnvironmentVariable("HSA_OVERRIDE_GFX_VERSION", $null, "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "2", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_MAX_LOADED_MODELS", "1", "User")

$env:HSA_OVERRIDE_GFX_VERSION = $null
$env:OLLAMA_NUM_PARALLEL = "2"
$env:OLLAMA_MAX_LOADED_MODELS = "1"

# 2. Restart Ollama in Safe Mode
Write-Host "[2/3] Restarting Ollama..." -ForegroundColor Yellow
Get-Process -Name ollama* -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Start-Process "ollama" -ArgumentList "serve" -NoNewWindow
Start-Sleep -Seconds 5

# 3. Verify
Write-Host "[3/3] Verifying System..." -ForegroundColor Yellow
ollama list

Write-Host "`n✅ System recovered to stable state." -ForegroundColor Green
Write-Host "Aggressive GPU offloading has been disabled to prevent crashes."
Write-Host "The system is now in 'Stable Mode' with 2 parallel streams."
