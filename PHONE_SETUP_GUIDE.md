# 📱 Android Phone Setup: Anti-Theft GPS & Intruder Selfie

এই গাইডে বলা আছে কীভাবে আপনার অ্যান্ড্রয়েড ফোন দিয়ে:
1. ফোন আনলক করার চেষ্টা করলেই অজান্তে ফ্রন্ট ক্যামেরা দিয়ে **চোরের সেলফি** তুলবে।
2. ফোনের **লাইভ জিপিএস লোকেশন ও ছবি** স্বয়ংক্রিয়ভাবে আপনার পাইথন ড্যাশবোর্ডে পাঠাবে।
3. ইন্টারনেট বা জিপিএস অফ করার চেষ্টা করলে চোরকে বাধা দেবে।

---

## ধাপ ১: সিক্রেট সেলফি তোলার সিস্টেম (কোনো কোডিং ছাড়া সবচেয়ে কার্যকর)

Google Play Store-এ কিছু বিশ্বস্ত ও ফ্রি অ্যাপ রয়েছে যা বিশেষ করে চোরের ছবি তুলতে ডিজাইন করা:

### অ্যাপ অপশন A: **CrookCatcher** অথবা **Lockwatch** (সবচেয়ে সহজ)
1. **Play Store** থেকে `CrookCatcher - Anti Theft` অথবা `Lockwatch - Thief Catcher` ইনস্টল করুন।
2. অ্যাপটি ওপেন করে `Device Admin Permission` এবং `Camera + Location Permission` দিন।
3. **সেটিংস:**
   * **Failed unlock attempts:** `1` বা `2` সিলেক্ট করুন। (অর্থাৎ কেউ ভুল প্যাটার্ন বা পিন দিলে সাথে সাথে সেলফি তুলবে)।
   * অ্যাপটি স্বয়ংক্রিয়ভাবে ফ্রন্ট ক্যামেরা দিয়ে নিঃশব্দে ছবি তুলে আপনার নির্ধারিত **ইমেইলে (Gmail)** লোকেশন ম্যাপ লিংকসহ পাঠিয়ে দেবে!

---

## ধাপ ২: আপনার নিজের পাইথন সার্ভারে ছবি ও জিপিএস পাঠানোর পদ্ধতি (MacroDroid)

যদি আপনি সরাসরি আপনার পাইথন সার্ভারেই (`app.py`) ফটো এবং জিপিএস আনতে চান:

1. **Play Store** থেকে `MacroDroid - Device Automation` ইনস্টল করুন।
2. একটি নতুন **Macro** তৈরি করুন:
   * **Trigger:** `Failed Login Attempt` (ভুল পিন/প্যাটার্ন দিলে) অথবা `SMS Received` (গোপন কোড এসএমএস পেলে)।
   * **Action 1:** `Take Picture` -> Front Camera (No preview / নিঃশব্দে)।
   * **Action 2:** `HTTP Request (POST)`:
     * **URL:** `http://<YOUR_IP_OR_NGROK_URL>:5000/api/upload`
     * **Body Content Type:** `Multipart form-data`
     * **Parameters:** 
       * `lat` = `[location_lat]`
       * `lon` = `[location_lon]`
       * `battery` = `[battery]`
       * `photo` = (ক্যাপচার করা ছবি সিলেক্ট করুন)
3. সেভ করে দিন। এখন চোর ভুল পিন দিলে বা আপনি রিমোটলি ট্রিপ করলেই পাইথন সার্ভারে ডিরেক্ট ছবি চলে আসবে।

---

## ধাপ ৩: চোর যেন ডাটা/লোকেশন অফ বা ফোন সুইচ অফ করতে না পারে

1. আপনার ফোনের **Settings > Lock Screen > Secure Lock Settings**-এ যান।
2. **"Lock network and security"** অপশনটি **ON** করুন।
   * এর ফলে ফোন লক থাকা অবস্থায় ওপরের নোটিফিকেশন বার নামিয়ে কেউ Mobile Data, Wi-Fi, Airplane Mode বা GPS অফ করতে পারবে না।
   * এমনকি ফোন Power Off (সুইচ অফ) করতে গেলেও স্ক্রিন লক আনলক করতে হবে!
