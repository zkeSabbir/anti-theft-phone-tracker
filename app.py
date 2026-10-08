import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_from_directory

from mobile_client import register_mobile_client

app = Flask(__name__)
register_mobile_client(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_DIR = os.path.join(BASE_DIR, 'captured_photos')
AUDIO_DIR = os.path.join(BASE_DIR, 'recorded_audio')
DB_PATH = os.path.join(BASE_DIR, 'tracker.db')

os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# ডাটাবেস ইনিশিয়ালাইজেশন (অ্যাডভান্সড ফিচারসহ)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lon REAL,
            speed REAL,
            battery INTEGER,
            charging INTEGER,
            network_type TEXT,
            accuracy REAL,
            timestamp TEXT,
            photo_filename TEXT,
            audio_filename TEXT,
            event_type TEXT
        )
    ''')
    # রিমোট কমান্ড টেবিল (ফোন হারিয়ে গেলে সার্ভার থেকে কমান্ড পাঠানো: Siren, Lock, etc.)
    c.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT,
            created_at TEXT,
            executed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/api/upload', methods=['POST'])
def receive_data():
    """
    মোবাইল অ্যাপ থেকে তথ্য গ্রহণ:
    - GPS Coordinates (Lat, Lon, Speed)
    - Intruder Selfie Photo
    - Ambient Audio Clip (ঐচ্ছিক)
    - Battery, Charging, Network Status
    - Event Type (Wrong Password, Remote Trigger, Periodic Tracker)
    """
    lat = request.form.get('lat') or (request.json.get('lat') if request.is_json else None)
    lon = request.form.get('lon') or (request.json.get('lon') if request.is_json else None)
    speed = request.form.get('speed', 0)
    battery = request.form.get('battery') or (request.json.get('battery') if request.is_json else None)
    charging = request.form.get('charging', 0)
    network_type = request.form.get('network_type', 'Unknown')
    accuracy = request.form.get('accuracy', 0)
    event_type = request.form.get('event_type', 'AUTO_TRACK')
    
    photo_file = request.files.get('photo')
    audio_file = request.files.get('audio')
    
    photo_filename = None
    audio_filename = None
    time_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ইন্ট্রুডার সেলফি সেভ
    if photo_file:
        photo_filename = f"intruder_{time_tag}.jpg"
        photo_file.save(os.path.join(PHOTO_DIR, photo_filename))
        print(f"[+] Intruder photo saved: {photo_filename}")

    # আশেপাশের অডিও সেভ
    if audio_file:
        audio_filename = f"audio_{time_tag}.mp3"
        audio_file.save(os.path.join(AUDIO_DIR, audio_filename))
        print(f"[+] Ambient audio recorded: {audio_filename}")

    # ডাটাবেসে লগ রাখা
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO locations (lat, lon, speed, battery, charging, network_type, accuracy, timestamp, photo_filename, audio_filename, event_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        float(lat) if lat else 0.0,
        float(lon) if lon else 0.0,
        float(speed) if speed else 0.0,
        battery,
        1 if str(charging) in ['1', 'true', 'True'] else 0,
        network_type,
        accuracy,
        now_str,
        photo_filename,
        audio_filename,
        event_type
    ))
    conn.commit()

    # কোনো পেন্ডিং কমান্ড আছে কিনা যা ফোন এক্সিকিউট করবে (যেমন SIREN, FLASH)
    c.execute('SELECT id, command FROM commands WHERE executed = 0 ORDER BY id DESC LIMIT 1')
    pending_cmd = c.fetchone()
    cmd_to_send = None
    if pending_cmd:
        cmd_id, cmd_to_send = pending_cmd
        c.execute('UPDATE commands SET executed = 1 WHERE id = ?', (cmd_id,))
        conn.commit()
    conn.close()

    print(f"[+] Update Received: Event={event_type}, Lat={lat}, Lon={lon}, Battery={battery}%")

    return jsonify({
        "status": "success",
        "command": cmd_to_send
    }), 200


@app.route('/api/command', methods=['POST'])
def send_remote_command():
    """ড্যাশবোর্ড থেকে ফোনে রিমোট কমান্ড পাঠানো (যেমন: siren, snap_photo, flash_light)"""
    cmd = request.json.get('command')
    if cmd:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO commands (command, created_at) VALUES (?, ?)', 
                  (cmd, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return jsonify({"status": "command_queued", "command": cmd}), 200
    return jsonify({"error": "No command provided"}), 400


@app.route('/api/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM locations ORDER BY id DESC LIMIT 60')
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route('/photos/<filename>')
def serve_photo(filename):
    return send_from_directory(PHOTO_DIR, filename)

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)


@app.route('/')
def dashboard():
    with open(os.path.join(BASE_DIR, 'index.html'), 'r', encoding='utf-8') as f:
        return f.read()

if __name__ == '__main__':
    print("[+] Anti-Theft Command & Tracker Server running at: https://localhost:5000")
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc', debug=True)
