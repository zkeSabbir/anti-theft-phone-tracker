package com.mysecurity.tracker;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.telephony.SmsManager;
import android.telephony.SubscriptionInfo;
import android.telephony.SubscriptionManager;
import android.telephony.TelephonyManager;
import android.util.Log;

import java.util.List;

/**
 * সিম পরিবর্তন ডিটেক্টর:
 * চোর যদি আপনার সিম খুলে নিজের নতুন কোনো সিম ঢুকিয়ে ফোন অন করে,
 * সাথে সাথে অ্যাপটি চোরের নতুন সিম থেকে আপনার পরিবারের নাম্বারে সিক্রেট SMS পাঠিয়ে দেবে!
 */
public class SimChangeReceiver extends BroadcastReceiver {
    private static final String TAG = "SimChangeSecurity";

    // আপনার পরিবারের বা বিশ্বস্ত বিকল্প ব্যাকআপ মোবাইল নম্বর
    public static final String TRUSTED_BACKUP_PHONE = "+8801XXXXXXXXX"; 
    private static final String PREF_SIM_SERIAL = "registered_sim_serial";

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(action) || "android.intent.action.SIM_STATE_CHANGED".equals(action)) {
            checkSimCardChange(context);
        }
    }

    private void checkSimCardChange(Context context) {
        SharedPreferences prefs = context.getSharedPreferences("security_prefs", Context.MODE_PRIVATE);
        String savedSimSerial = prefs.getString(PREF_SIM_SERIAL, null);

        TelephonyManager tm = (TelephonyManager) context.getSystemService(Context.LOCATION_SERVICE);
        SubscriptionManager sm = (SubscriptionManager) context.getSystemService(Context.TELEPHONY_SUBSCRIPTION_SERVICE);

        try {
            if (sm != null) {
                List<SubscriptionInfo> subs = sm.getActiveSubscriptionInfoList();
                if (subs != null && !subs.isEmpty()) {
                    String currentSimSerial = subs.get(0).getIccId();

                    if (savedSimSerial == null) {
                        // প্রথমবার অ্যাপ ইনস্টল করার পর আপনার বর্তমান আসল সিম সেভ হলো
                        prefs.edit().putString(PREF_SIM_SERIAL, currentSimSerial).apply();
                        Log.d(TAG, "Trusted owner SIM registered: " + currentSimSerial);
                    } else if (!savedSimSerial.equals(currentSimSerial)) {
                        // 🚨 চোর নতুন সিম ঢুকিয়েছে!
                        String thiefNumber = subs.get(0).getNumber();
                        Log.e(TAG, "🚨 STOLEN PHONE ALERT: NEW SIM DETECTED! Number: " + thiefNumber);

                        String alertMsg = "🚨 STOLEN PHONE ALERT!\nA new SIM has been inserted in your stolen phone.\nNew SIM Number: " 
                                        + (thiefNumber != null ? thiefNumber : "Unknown") 
                                        + "\nSerial: " + currentSimSerial;

                        SmsManager.getDefault().sendTextMessage(TRUSTED_BACKUP_PHONE, null, alertMsg, null, null);
                    }
                }
            }
        } catch (SecurityException e) {
            Log.e(TAG, "SIM Permission missing", e);
        }
    }
}
