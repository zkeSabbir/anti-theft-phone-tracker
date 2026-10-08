package com.mysecurity.tracker;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

public class MyDeviceAdminReceiver extends DeviceAdminReceiver {
    private static final String TAG = "AntiTheftReceiver";

    @Override
    public void onPasswordFailed(Context context, Intent intent) {
        super.onPasswordFailed(context, intent);
        Log.d(TAG, "🚨 ALERT: Wrong password attempt detected!");

        // চোর ভুল পাসওয়ার্ড দিলেই ব্যাকগ্রাউন্ড সার্ভিস চালু হবে (সেলফি + জিপিএস তুলতে)
        Intent serviceIntent = new Intent(context, IntruderCaptureService.class);
        serviceIntent.putExtra("EVENT_TYPE", "WRONG_PIN");
        context.startForegroundService(serviceIntent);
    }

    @Override
    public void onPasswordSucceeded(Context context, Intent intent) {
        super.onPasswordSucceeded(context, intent);
        Log.d(TAG, "Device unlocked successfully by real owner.");
    }
}
