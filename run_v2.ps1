
# TRM Swarm V2 Launcher
# Kill existing processes
Get-Process -Name node, python -ErrorAction SilentlyContinue | Stop-Process -Force

# Activate Venv & Set PYTHONPATH
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."

# Stable GPU Tuning (Vulkan) for 6700XT
$env:OLLAMA_VULKAN = "1"
$env:OLLAMA_NUM_PARALLEL = "2"
$env:OLLAMA_MAX_LOADED_MODELS = "2"

# Deepseek API Key
$env:DEEPSEEK_API_KEY = "sk-8216243fb680414dab9f149d31a54e37"

# OpenRouter API Key
$env:OPENROUTER_API_KEY = "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"

# Gemini API Key
$env:GEMINI_API_KEY = "AIzaSyDVnLH-OV8dtSZrYGAYYM_Mbz7ZkVVjOr4"

# Start MCP Synthesized Tools
Write-Host "Starting MCP Synthesized Tools..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\Activate.ps1; `$env:PYTHONPATH = '.'; python start_tools.py" -NoNewWindow
Start-Sleep -Seconds 5

# Start API V2 in Background
Write-Host "Starting Swarm V2 API (Vulkan GPU Enabled)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\Activate.ps1; `$env:PYTHONPATH = '.'; `$env:OLLAMA_VULKAN = '1'; `$env:OLLAMA_NUM_PARALLEL = '2'; `$env:OLLAMA_MAX_LOADED_MODELS = '2'; uvicorn swarm_v2.app_v2:app --host 0.0.0.0 --port 8001" -NoNewWindow

# Wait for API to warm up
Start-Sleep -Seconds 5

# Start Dashboard (Upgraded v2)
Write-Host "Starting Swarm Dashboard V2 on Port 5173..." -ForegroundColor Cyan
Set-Location swarm_v2_artifacts/dashboard-v2
npm install
npx vite --port 5173 --host 127.0.0.1
