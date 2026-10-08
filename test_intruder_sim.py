import requests
import time
import os

SERVER_URL = "http://127.0.0.1:5000/api/upload"

print("[*] Simulating Intruder Wrong Password Attempt with GPS and Photo...")

# ১. সাধারণ ট্র্যাকিং ইভেন্ট
requests.post(SERVER_URL, data={
    "lat": 23.8103,
    "lon": 90.4125,
    "speed": 0,
    "battery": 82,
    "charging": 0,
    "event_type": "PERIODIC_TRACK"
})

time.sleep(1)

# ২. ইন্ট্রুডার ভুল পিন দিল -> ক্যামেরা দিয়ে সেলফি ক্যাপচার হলো
test_photo_path = "test_intruder.jpg"
with open(test_photo_path, "wb") as f:
    f.write(os.urandom(1024 * 50)) # ডামি ইমেজ ডাটা

with open(test_photo_path, "rb") as f:
    files = {"photo": ("intruder.jpg", f, "image/jpeg")}
    data = {
        "lat": 23.8135,
        "lon": 90.4148,
        "speed": 15,
        "battery": 80,
        "charging": 0,
        "event_type": "WRONG_PIN"
    }
    res = requests.post(SERVER_URL, data=data, files=files)
    print(f"Intruder Event Response: {res.status_code}, Received Command: {res.json().get('command')}")

print("[OK] Test Finished. Visit http://localhost:5000 to see map & intruder photo.")
