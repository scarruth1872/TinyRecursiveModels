set PYTHONPATH=.
set DEEPSEEK_API_KEY=sk-7c4b20766830484cb1eca2b6737109e2
set OPENROUTER_API_KEY=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
set GEMINI_API_KEY=AIzaSyDVnLH-OV8dtSZrYGAYYM_Mbz7ZkVVjOr4

python -u -m uvicorn swarm_v2.app_v2:app --port 8001 --host 0.0.0.0 > uvicorn_server.log 2>&1
