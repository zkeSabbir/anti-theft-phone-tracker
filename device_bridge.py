import subprocess
import time
import requests
import json
import re

ADB_IP_PORT = "192.168.0.101:40273"
SERVER_URL = "http://127.0.0.1:5000/api/upload"

def get_adb_path():
    cmd = 'powershell -Command "(Get-ChildItem -Path \\"$env:LOCALAPPDATA\\Microsoft\\WinGet\\Packages\\" -Filter \\"adb.exe\\" -Recurse).FullName"'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip().split('\n')[0].strip()

ADB_PATH = get_adb_path()

def adb_exec(command):
    full_cmd = f'"{ADB_PATH}" -s {ADB_IP_PORT} {command}'
    try:
        res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=10)
        return res.stdout.strip()
    except Exception as e:
        return ""

def connect_adb():
    subprocess.run(f'"{ADB_PATH}" connect {ADB_IP_PORT}', shell=True, capture_output=True)

print("[*] Starting Background Bridge for HONOR 400 (DNY-NX9)...")
connect_adb()

def sync_device_state():
    # ব্যাটারি ও চার্জিং স্টেট রিড
    batt_out = adb_exec("shell dumpsys battery")
    battery = 85
    charging = 0
    for line in batt_out.split('\n'):
        if "level:" in line:
            battery = int(line.split(':')[1].strip())
        if "status:" in line and "2" in line:
            charging = 1

    # জিপিএস কোঅর্ডিনেট
    loc_out = adb_exec("shell dumpsys location")
    lat, lon = 23.8103, 90.4125
    # ডাম্পসিস লোকেশন পার্সিং
    match = re.search(r'Location\[(?:fused|network)\s+([0-9\.]+),([0-9\.]+)', loc_out)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))

    # সার্ভারে পোস্ট করা
    data = {
        "lat": lat,
        "lon": lon,
        "speed": 0,
        "battery": battery,
        "charging": charging,
        "event_type": "LIVE_TELEMETRY"
    }

    try:
        r = requests.post(SERVER_URL, data=data, timeout=5)
        if r.status_code == 200:
            cmd = r.json().get("command")
            if cmd == "SIREN":
                print("[!] Triggering Emergency Siren on phone...")
                adb_exec("shell cmd media_session volume --show --stream 3 --set 15")
                adb_exec("shell cmd media_session volume --show --stream 4 --set 15")
            elif cmd == "FAKEOFF":
                print("[!] Triggering Fake Shutdown on phone...")
                adb_exec("shell input keyevent 26") # স্ক্রিন অফ
    except Exception as e:
        pass

if __name__ == '__main__':
    print("[+] Bridge Active. Syncing Phone Telemetry to Dashboard every 5s...")
    while True:
        try:
            sync_device_state()
        except Exception as e:
            pass
        time.sleep(5)
