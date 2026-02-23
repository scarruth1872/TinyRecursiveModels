
# Start Backend
Start-Process -NoNewWindow powershell -ArgumentList "-Command .\venv\Scripts\Activate.ps1; python app.py"

# Start Frontend
cd dashboard
npm run dev
