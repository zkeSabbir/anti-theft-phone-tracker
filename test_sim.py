import requests
import time

SERVER_URL = "http://127.0.0.1:5000/api/upload"

# সিমুলেশন ডাটা: ফোন বিভিন্ন জায়গায় ঘুরছে এবং একবার ভুল পিন দেওয়ায় সেলফি উঠছে
locations_trail = [
    {"lat": 23.8103, "lon": 90.4125, "battery": 88},
    {"lat": 23.8120, "lon": 90.4140, "battery": 87},
    {"lat": 23.8145, "lon": 90.4162, "battery": 85},
]

print("[*] Testing Phone Tracker Server with simulated GPS...")

for loc in locations_trail:
    res = requests.post(SERVER_URL, data=loc)
    print(f"Sent: {loc['lat']}, {loc['lon']} -> Status: {res.status_code}")
    time.sleep(1)

print("[OK] Test Completed! Refresh dashboard at http://localhost:5000")
