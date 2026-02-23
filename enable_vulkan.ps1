
# Swarm V2: Vulkan GPU Enablement
# Switches from ROCm to Vulkan for broader AMD compatibility on Windows

Write-Host "--- Ollama Vulkan GPU Enablement ---" -ForegroundColor Cyan

# 1. Reset ROCm overrides and enable Vulkan
Write-Host "[1/3] Switch to Vulkan Backend..." -ForegroundColor Yellow
[System.Environment]::SetEnvironmentVariable("HSA_OVERRIDE_GFX_VERSION", $null, "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_VULKAN", "1", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "2", "User")

$env:HSA_OVERRIDE_GFX_VERSION = $null
$env:OLLAMA_VULKAN = "1"
$env:OLLAMA_NUM_PARALLEL = "2"

# 2. Restart Ollama
Write-Host "[2/3] Restarting Ollama..." -ForegroundColor Yellow
Get-Process -Name ollama* -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Start-Process "ollama" -ArgumentList "serve" -NoNewWindow
Start-Sleep -Seconds 5

# 3. Test
Write-Host "[3/3] Running Vulkan Test..." -ForegroundColor Yellow
ollama run deepseek-r1:1.5b "hi" --verbose

Write-Host "`nChecking Ollama Status:" -ForegroundColor Cyan
ollama ps

Write-Host "`nIf you see 'GPU' or 'Vulkan' under PROCESSOR, we have success!" -ForegroundColor Green
