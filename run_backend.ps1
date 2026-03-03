$env:PYTHONPATH = '.'
$env:OPENROUTER_API_KEY = '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'
$env:DEEPSEEK_API_KEY = 'sk-7c4b20766830484cb1eca2b6737109e2'
$env:GEMINI_API_KEY = 'AIzaSyDVnLH-OV8dtSZrYGAYYM_Mbz7ZkVVjOr4'

Write-Host "[Local] Starting Swarm V2 Backend with Regional Manager LLM keys injected..."
python swarm_v2/app_v2.py 2>&1 | Tee-Object -FilePath backend.log
