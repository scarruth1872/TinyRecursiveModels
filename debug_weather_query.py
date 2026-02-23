import requests
try:
    url = "http://localhost:9110/data/2.5/weather?q=kernersville"
    r = requests.get(url)
    print(f"URL: {url} -> {r.status_code}")
    print("Body:", r.text)
except Exception as e:
    print("Error:", e)
