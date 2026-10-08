package com.mysecurity.tracker;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.*;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.MediaRecorder;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Bundle;
import android.os.IBinder;
import android.util.Log;

import androidx.core.app.NotificationCompat;

import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class IntruderCaptureService extends Service {
    private static final String TAG = "IntruderService";
    
    // আপনার পাইথন সার্ভার এর IP অ্যাড্রেস
    public static final String SERVER_URL = "http://192.168.0.100:5000/api/upload"; 

    private LocationManager locationManager;
    private double currentLat = 0.0;
    private double currentLon = 0.0;
    private float currentSpeed = 0.0f;

    @Override
    public void onCreate() {
        super.onCreate();
        startForegroundServiceNotification();
        initGPS();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String eventType = intent != null ? intent.getStringExtra("EVENT_TYPE") : "PERIODIC";
        Log.d(TAG, "Triggering capture for event: " + eventType);

        // ১. ফ্রন্ট ক্যামেরা দিয়ে নিঃশব্দে ছবি তোলা
        takeSecretFrontSelfie(eventType);

        return START_NOT_STICKY;
    }

    private void initGPS() {
        locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        try {
            if (locationManager != null && locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                locationManager.requestSingleUpdate(LocationManager.GPS_PROVIDER, new LocationListener() {
                    @Override
                    public void onLocationChanged(Location location) {
                        currentLat = location.getLatitude();
                        currentLon = location.getLongitude();
                        currentSpeed = location.getSpeed() * 3.6f; // km/h
                        Log.d(TAG, "GPS Updated: " + currentLat + ", " + currentLon);
                    }
                    @Override public void onStatusChanged(String p, int s, Bundle b) {}
                    @Override public void onProviderEnabled(String p) {}
                    @Override public void onProviderDisabled(String p) {}
                }, null);
            }
        } catch (SecurityException e) {
            Log.e(TAG, "Location permission error", e);
        }
    }

    private void takeSecretFrontSelfie(String eventType) {
        // Camera2 API দিয়ে কোনো প্রিভিউ ছাড়া ব্যাকগ্রাউন্ডে ছবি তোলা
        // ছবি তোলা শেষে uploadDataToServer(photoFile, eventType) কল হবে
        File photoFile = new File(getCacheDir(), "secret_selfie_" + System.currentTimeMillis() + ".jpg");
        // ডামি বা ফ্রন্ট ক্যামেরা লজিক সম্পন্ন হলে আপলোড কল হবে
        uploadDataToServer(photoFile, eventType);
    }

    private void uploadDataToServer(File photoFile, String eventType) {
        // ব্যাটারি তথ্য সংগ্রহ
        IntentFilter ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        Intent batteryStatus = registerReceiver(null, ifilter);
        int level = batteryStatus != null ? batteryStatus.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) : -1;
        int status = batteryStatus != null ? batteryStatus.getIntExtra(BatteryManager.EXTRA_STATUS, -1) : -1;
        boolean isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL;

        OkHttpClient client = new OkHttpClient();

        MultipartBody.Builder builder = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("lat", String.valueOf(currentLat))
                .addFormDataPart("lon", String.valueOf(currentLon))
                .addFormDataPart("speed", String.valueOf(currentSpeed))
                .addFormDataPart("battery", String.valueOf(level))
                .addFormDataPart("charging", String.valueOf(isCharging))
                .addFormDataPart("event_type", eventType);

        if (photoFile != null && photoFile.exists() && photoFile.length() > 0) {
            builder.addFormDataPart("photo", photoFile.getName(),
                    RequestBody.create(photoFile, MediaType.parse("image/jpeg")));
        }

        Request request = new Request.Builder()
                .url(SERVER_URL)
                .post(builder.build())
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.e(TAG, "Upload failed to python server: " + e.getMessage());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    String respStr = response.body().string();
                    Log.d(TAG, "Server Response: " + respStr);
                    try {
                        JSONObject json = new JSONObject(respStr);
                        String cmd = json.optString("command");
                        if ("SIREN".equalsIgnoreCase(cmd)) {
                            playHighAlarmSiren();
                        }
                    } catch (Exception ignored) {}
                }
            }
        });
    }

    // চোর ধরা পড়লে বা ড্যাশবোর্ড থেকে নির্দেশ পেলে ১০০% ভলিউমে সাইরেন বাজানো
    private void playHighAlarmSiren() {
        try {
            AudioManager audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
            if (audioManager != null) {
                audioManager.setStreamVolume(AudioManager.STREAM_ALARM,
                        audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM), 0);
            }
            MediaPlayer mediaPlayer = MediaPlayer.create(this, android.provider.Settings.System.DEFAULT_ALARM_ALERT_URI);
            if (mediaPlayer != null) {
                mediaPlayer.setLooping(true);
                mediaPlayer.start();
            }
        } catch (Exception e) {
            Log.e(TAG, "Error playing siren", e);
        }
    }

    private void startForegroundServiceNotification() {
        String channelId = "security_channel";
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(channelId, "Security Guard", NotificationManager.IMPORTANCE_LOW);
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) manager.createNotificationChannel(channel);
        }
        Notification notification = new NotificationCompat.Builder(this, channelId)
                .setContentTitle("Device Security Protected")
                .setContentText("Anti-Theft Active")
                .setSmallIcon(android.R.drawable.ic_lock_idle_lock)
                .build();
        startForeground(101, notification);
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
