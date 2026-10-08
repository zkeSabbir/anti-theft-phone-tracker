import os
from flask import send_from_directory, render_template_string

def register_mobile_client(app):
    @app.route('/mobile')
    def mobile_tracker_client():
        """
        মোবাইল থেকে এই পেজটি ওপেন করলেই কোনো অ্যাপ ছাড়া সরাসরি:
        - লাইভ জিপিএস কোঅর্ডিনেট রিড করবে
        - ব্যাটারি পারসেন্টেজ ও চার্জিং স্টেট রিড করবে
        - ফ্রন্ট ক্যামেরা দিয়ে চোর বা ইন্ট্রুডার টেস্ট ছবি তুলবে
        - এবং সার্ভারে স্বয়ংক্রিয়ভাবে পাঠাবে
        """
        html = """
        <!DOCTYPE html>
        <html lang="bn">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Anti-Theft Mobile Guard</title>
            <style>
                body { background: #0f172a; color: #fff; font-family: sans-serif; text-align: center; padding: 25px 15px; }
                .card { background: #1e293b; border-radius: 14px; padding: 20px; border: 1px solid #334155; max-width: 380px; margin: 0 auto; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
                h2 { color: #38bdf8; font-size: 1.25rem; margin-bottom: 12px; }
                p { color: #94a3b8; font-size: 0.9rem; line-height: 1.5; margin-bottom: 20px; }
                .btn { display: block; width: 100%; padding: 14px; border: none; border-radius: 8px; font-size: 1rem; font-weight: bold; cursor: pointer; margin-bottom: 12px; }
                .btn-primary { background: #0284c7; color: white; }
                .btn-danger { background: #e11d48; color: white; }
                #status { margin-top: 15px; font-size: 0.85rem; color: #34d399; font-weight: bold; }
                video, canvas { display: none; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🛡️ Anti-Theft Guard Test</h2>
                <p>আপনার মোবাইল থেকে সরাসরি GPS লোকেশন ও সেলফি ক্যামেরা টেস্ট করার প্যানেল।</p>
                
                <button class="btn btn-primary" onclick="startTracking()">📡 ১. লাইভ GPS ট্র্যাকিং শুরু করুন</button>
                <button class="btn btn-danger" onclick="triggerCameraCapture()">📸 ২. ইন্ট্রুডার সেলফি টেস্ট</button>
                <button class="btn" style="background:#f59e0b; color:#000;" onclick="testFakeShutdown()">🌑 ৩. ফেক শাটডাউন টেস্ট (স্ক্রিন ব্ল্যাক)</button>
                <button class="btn" style="background:#ec4899; color:#fff;" onclick="testLoudSiren()">📢 ৪. লাউড সাইরেন টেস্ট</button>
                <input type="file" id="cameraInput" accept="image/*" capture="user" style="display:none;" onchange="handleFileCapture(this)">
                
                <div id="status">স্ট্যাটাস: রেডি</div>
            </div>

            <!-- ফেক শাটডাউন ফুল স্ক্রিন ব্ল্যাক ওভারলে -->
            <div id="fakeBlackScreen" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:#000; z-index:99999; flex-direction:column; align-items:center; justify-content:center; color:#111;">
                <p style="font-size:0.75rem; color:#222; text-align:center; padding:20px;">
                    [Fake Shutdown Active]<br>
                    আনলক করতে স্ক্রিনে ৩ বার দ্রুত ট্যাপ করুন অথবা ভলিউম বাটন চাপুন।
                </p>
            </div>

            <video id="webcam" autoplay playsinline></video>
            <canvas id="canvas"></canvas>

            <script>
                var watchId = null;
                var batteryLevel = 85;
                var isCharging = false;

                if ('getBattery' in navigator) {
                    navigator.getBattery().then(function(b) {
                        batteryLevel = Math.round(b.level * 100);
                        isCharging = b.charging;
                    });
                }

                function logStatus(msg, isErr) {
                    var el = document.getElementById('status');
                    el.innerText = msg;
                    el.style.color = isErr ? '#f43f5e' : '#34d399';
                }

                function sendToServer(lat, lon, speed, photoBlob, eventType) {
                    var fd = new FormData();
                    fd.append('lat', lat);
                    fd.append('lon', lon);
                    fd.append('speed', speed || 0);
                    fd.append('battery', batteryLevel);
                    fd.append('charging', isCharging ? 1 : 0);
                    fd.append('event_type', eventType);

                    if (photoBlob) {
                        fd.append('photo', photoBlob, 'mobile_capture.jpg');
                    }

                    fetch('/api/upload', {
                        method: 'POST',
                        body: fd
                    })
                    .then(r => r.json())
                    .then(data => {
                        logStatus("✅ সার্ভারে পাঠানো হয়েছে! (Event: " + eventType + ")");
                        if (data.command === 'SIREN') {
                            alert("🚨 সার্ভার থেকে সাইরেন কমান্ড এসেছে!");
                        }
                    })
                    .catch(e => logStatus("❌ সার্ভার কানেকশন এরর: " + e, true));
                }

                function startTracking() {
                    if (!navigator.geolocation) {
                        logStatus("GPS নট সাপোর্টেড", true);
                        return;
                    }
                    logStatus("GPS লোকেশন খোঁজা হচ্ছে...");
                    watchId = navigator.geolocation.watchPosition(function(pos) {
                        var lat = pos.coords.latitude;
                        var lon = pos.coords.longitude;
                        var speed = pos.coords.speed ? Math.round(pos.coords.speed * 3.6) : 0;
                        logStatus("📍 লাইভ অবস্থান: " + lat.toFixed(4) + ", " + lon.toFixed(4));
                        sendToServer(lat, lon, speed, null, "LIVE_GPS");
                    }, function(err) {
                        logStatus("GPS পারমিশন ডিনাইড: " + err.message, true);
                    }, { enableHighAccuracy: true });
                }

                function triggerCameraCapture() {
                    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                        simulateIntruderTest();
                    } else {
                        // HTTP তে ব্রাউজার সিকিউরিটির কারণে সরাসরি ক্যামেরা খুলতে ফাইল ইনপুট ট্রিগার
                        logStatus("ক্যামেরা ওপেন হচ্ছে...");
                        document.getElementById('cameraInput').click();
                    }
                }

                function handleFileCapture(input) {
                    if (input.files && input.files[0]) {
                        var file = input.files[0];
                        logStatus("ছবি আপলোড হচ্ছে...");
                        if (navigator.geolocation) {
                            navigator.geolocation.getCurrentPosition(function(pos) {
                                sendToServer(pos.coords.latitude, pos.coords.longitude, 0, file, "WRONG_PIN");
                            }, function() {
                                sendToServer(23.8103, 90.4125, 0, file, "WRONG_PIN");
                            });
                        } else {
                            sendToServer(23.8103, 90.4125, 0, file, "WRONG_PIN");
                        }
                    }
                }

                async function simulateIntruderTest() {
                    logStatus("📸 সেলফি ক্যামেরা ওপেন হচ্ছে...");
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({
                            video: { facingMode: "user" },
                            audio: false
                        });
                        const video = document.getElementById('webcam');
                        video.srcObject = stream;
                        
                        setTimeout(() => {
                            const canvas = document.getElementById('canvas');
                            canvas.width = video.videoWidth || 640;
                            canvas.height = video.videoHeight || 480;
                            const ctx = canvas.getContext('2d');
                            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                            
                            stream.getTracks().forEach(t => t.stop());

                            canvas.toBlob(blob => {
                                navigator.geolocation.getCurrentPosition(pos => {
                                    sendToServer(pos.coords.latitude, pos.coords.longitude, 0, blob, "WRONG_PIN");
                                }, () => {
                                    sendToServer(23.8103, 90.4125, 0, blob, "WRONG_PIN");
                                });
                            }, 'image/jpeg');
                        }, 1200);
                    } catch (e) {
                        logStatus("ক্যামেরা এরর: " + e.message, true);
                    }
                }

                // ৩. ফেক শাটডাউন টেস্ট
                var tapCount = 0;
                function testFakeShutdown() {
                    var el = document.getElementById('fakeBlackScreen');
                    el.style.display = 'flex';
                    logStatus("🌑 ফোন ফেক শাটডাউন মোডে গেছে (স্ক্রিন ব্ল্যাক)");

                    // ওয়েক-আপ সিক্রেট লজিক: স্ক্রিনে ৩ বার ট্যাপ করলেই আবার খুলবে
                    el.onclick = function() {
                        tapCount++;
                        if (tapCount >= 3) {
                            el.style.display = 'none';
                            tapCount = 0;
                            logStatus("✨ আসল মালিকের সিক্রেট ট্যাপে ফোন ওয়েক-আপ হয়েছে!");
                        }
                    };
                }

                // ৪. লাউড সাইরেন টেস্ট
                function testLoudSiren() {
                    logStatus("📢 হাই ভলিউম সাইরেন বাজছে...");
                    try {
                        var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                        var osc = audioCtx.createOscillator();
                        var gainNode = audioCtx.createGain();
                        
                        osc.type = 'sawtooth';
                        osc.frequency.setValueAtTime(800, audioCtx.currentTime);
                        osc.frequency.exponentialRampToValueAtTime(1500, audioCtx.currentTime + 0.4);

                        gainNode.gain.setValueAtTime(1, audioCtx.currentTime);

                        osc.connect(gainNode);
                        gainNode.connect(audioCtx.destination);

                        osc.start();
                        setTimeout(function() {
                            osc.stop();
                            audioCtx.close();
                            logStatus("সাইরেন সম্পন্ন হয়েছে");
                        }, 3000);
                    } catch(e) {
                        alert("সাইরেন অডিও এরর: " + e.message);
                    }
                }
            </script>
        </body>
        </html>
        """
        return render_template_string(html)
