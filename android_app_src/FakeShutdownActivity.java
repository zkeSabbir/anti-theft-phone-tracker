package com.mysecurity.tracker;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;

/**
 * ফেক শাটডাউন স্ক্রিন:
 * স্ক্রিন পুরোপুরি ব্ল্যাক থাকবে, কোনো ব্যাক বা হোম কাজ করবে না।
 * শুধু আসল মালিক 'Volume Up + Volume Down' একসাথে চাপলেই এটি খুলবে।
 */
public class FakeShutdownActivity extends Activity {

    private boolean isVolumeUpPressed = false;
    private boolean isVolumeDownPressed = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // স্ক্রিনকে ফুল ব্ল্যাক ও ব্রাইটনেস শূন্য করে দেওয়া
        getWindow().addFlags(
                WindowManager.LayoutParams.FLAG_FULLSCREEN |
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON |
                WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD |
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
        );

        WindowManager.LayoutParams params = getWindow().getAttributes();
        params.screenBrightness = 0.01f; // সর্বনিম্ন ব্রাইটনেস
        getWindow().setAttributes(params);

        View blackView = new View(this);
        blackView.setBackgroundColor(0xFF000000); // ১০০% কালো স্ক্রিন
        setContentView(blackView);

        // চার্জার লাগালে অটোমেটিক ওয়েক-আপ লিসেনার
        IntentFilter filter = new IntentFilter(Intent.ACTION_POWER_CONNECTED);
        registerReceiver(chargerReceiver, filter);
    }

    private final BroadcastReceiver chargerReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            // আসল মালিক চার্জার লাগালে ফোন আবার স্বাভাবিক হয়ে যাবে
            finish();
        }
    };

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        // সিক্রেট আনলক ট্রিক: Volume Up + Volume Down একসাথে ৩ সেকেন্ড
        if (keyCode == KeyEvent.KEYCODE_VOLUME_UP) {
            isVolumeUpPressed = true;
        } else if (keyCode == KeyEvent.KEYCODE_VOLUME_DOWN) {
            isVolumeDownPressed = true;
        }

        if (isVolumeUpPressed && isVolumeDownPressed) {
            // আসল মালিক সিক্রেট কম্বিনেশন দিয়েছে -> ফেক শাটডাউন শেষ!
            finish();
            return true;
        }

        // চোর যাতে পাওয়ার বা অন্য কোনো কি চেপে বের হতে না পারে
        return true; 
    }

    @Override
    public boolean onKeyUp(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_VOLUME_UP) isVolumeUpPressed = false;
        if (keyCode == KeyEvent.KEYCODE_VOLUME_DOWN) isVolumeDownPressed = false;
        return true;
    }

    @Override
    public void onBackPressed() {
        // ব্যাক বাটন ডিজেবল
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        try {
            unregisterReceiver(chargerReceiver);
        } catch (Exception ignored) {}
    }
}
