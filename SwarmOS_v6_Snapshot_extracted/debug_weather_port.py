import requests
try:
    r = requests.get("http://localhost:9110/health")
    print("Health:", r.json())
    r2 = requests.get("http://localhost:9110/data/2.5/weather")
    print("Weather Path:", r2.status_code, r2.text)
except Exception as e:
    print("Error:", e)
