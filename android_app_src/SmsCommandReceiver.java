package com.mysecurity.tracker;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.BatteryManager;
import android.os.Bundle;
import android.os.IBinder;
import android.provider.Telephony;
import android.telephony.SmsManager;
import android.telephony.SmsMessage;
import android.util.Log;

/**
 * অফলাইন এসএমএস রেসপন্ডার:
 * ইন্টারনেট বা ওয়াইফাই ডাটা অফ থাকলেও সাধারণ SMS দিয়ে ফোন নিয়ন্ত্রণ:
 * - #LOC#  -> সাথে সাথে গুগল ম্যাপের লোকেশন লিংকসহ ফিরতি এসএমএস পাঠাবে।
 * - #SIREN# -> ফুল ভলিউমে সাইলেন্ট ভেঙে সাইরেন বাজাবে।
 * - #FAKE_OFF# -> ফেক শাটডাউন স্ক্রিন চালু করবে।
 */
public class SmsCommandReceiver extends BroadcastReceiver {
    private static final String TAG = "SmsSecurityReceiver";

    // আপনার সিক্রেট পাসকোড
    private static final String CMD_LOC = "#LOC#";
    private static final String CMD_SIREN = "#SIREN#";
    private static final String CMD_FAKE_OFF = "#FAKEOFF#";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (!Telephony.Sms.Intents.SMS_RECEIVED_ACTION.equals(intent.getAction())) return;

        SmsMessage[] messages = Telephony.Sms.Intents.getMessagesFromIntent(intent);
        if (messages == null) return;

        for (SmsMessage msg : messages) {
            String sender = msg.getDisplayOriginatingAddress();
            String body = msg.getMessageBody().trim();

            Log.d(TAG, "SMS Received from: " + sender + ", Content: " + body);

            if (body.contains(CMD_LOC)) {
                // ১. জিপিএস লোকেশন এসএমএস করা
                fetchAndReplyLocation(context, sender);
            } else if (body.contains(CMD_SIREN)) {
                // ২. সাইলেন্ট সাইরেন বাজানো
                Intent serviceIntent = new Intent(context, IntruderCaptureService.class);
                serviceIntent.putExtra("EVENT_TYPE", "REMOTE_SIREN");
                context.startForegroundService(serviceIntent);
            } else if (body.contains(CMD_FAKE_OFF)) {
                // ৩. ফেক শাটডাউন স্ক্রিন অন করা
                Intent fakeIntent = new Intent(context, FakeShutdownActivity.class);
                fakeIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(fakeIntent);
            }
        }
    }

    private void fetchAndReplyLocation(Context context, String replyNumber) {
        LocationManager lm = (LocationManager) context.getSystemService(Context.LOCATION_SERVICE);
        try {
            if (lm != null) {
                Location lastLoc = lm.getLastKnownLocation(LocationManager.GPS_PROVIDER);
                if (lastLoc == null) {
                    lastLoc = lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
                }

                if (lastLoc != null) {
                    double lat = lastLoc.getLatitude();
                    double lon = lastLoc.getLongitude();
                    String mapsUrl = "https://maps.google.com/?q=" + lat + "," + lon;
                    String reply = "🚨 Phone Security Alert!\nLocation: " + mapsUrl + "\nAccuracy: " + (int)lastLoc.getAccuracy() + "m";

                    SmsManager.getDefault().sendTextMessage(replyNumber, null, reply, null, null);
                    Log.d(TAG, "Location SMS sent to: " + replyNumber);
                } else {
                    SmsManager.getDefault().sendTextMessage(replyNumber, null, 
                        "🚨 Phone Alert: GPS locking in progress, try again in 1 min.", null, null);
                }
            }
        } catch (SecurityException e) {
            Log.e(TAG, "Permission error", e);
        }
    }
}
