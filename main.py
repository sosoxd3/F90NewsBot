import feedparser
import requests
import time
import re
from html import unescape
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8340084044:AAH4xDclN0yKECmpTFcnL5eshA4-qREHw4w")
CHAT_ID = os.getenv("CHAT_ID", "@f90newsnow")

# المصادر العربية
SOURCES = [
    "https://www.aljazeera.net/xml/rss/all.xml",
    "https://www.skynewsarabia.com/web/rss",
    "https://arabic.rt.com/rss/",
    "https://www.alarabiya.net/.mrss/ar.xml",
    "https://www.bbc.com/arabic/index.xml",
    "https://www.asharqnews.com/ar/rss.xml",
    "https://shehabnews.com/ar/rss.xml",
    "https://qudsn.co/feed",
    "https://maannews.net/rss/ar.xml"
]

# نص الحقوق والروابط
FOOTER = (
    "\n———\n"
    "📢 انضموا لنا لتَروا الأخبار لحظة بلحظة\n"
    "🌐 موقعنا: https://e9dd-009-80041-a80rjkupq6lz-deployed-internal.easysite.ai/\n"
    "📲 حمّل تطبيقنا للأندرويد: https://newoaks.s3.us-west-1.amazonaws.com/AutoDev/80041/d281064b-a82e-4fdf-bc19-d19cc4e0ccd4.apk\n"
    "📡 تابعنا على تيليجرام: https://t.me/f90newsnow"
)

seen = set()

def clean_text(s):
    s = unescape(s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def get_image(entry):
    for key in ("media_content", "media_thumbnail", "enclosures"):
        if key in entry:
            try:
                if isinstance(entry[key], list):
                    url = entry[key][0].get("url") or entry[key][0].get("href")
                else:
                    url = entry[key].get("url") or entry[key].get("href")
                if url and url.startswith("http"):
                    return url
            except Exception:
                continue
    if "summary" in entry:
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', entry["summary"])
        if m:
            return m.group(1)
    return None

def send_message(title, source, img=None):
    caption = f"📰 {clean_text(title)}\n📡 المصدر: {clean_text(source)}{FOOTER}"
    data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
    if img:
        data["photo"] = img
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data=data)
    else:
        data = {"chat_id": CHAT_ID, "text": caption, "parse_mode": "HTML"}
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=data)

def main():
    print("🚀 F90 News Arabic Bot بدأ العمل")
    while True:
        new_count = 0
        for url in SOURCES:
            try:
                feed = feedparser.parse(url)
                source = feed.feed.get("title", "خبر عاجل")
                for entry in reversed(feed.entries):  # الأقدم أولاً
                    link = entry.get("link")
                    if link and link not in seen:
                        seen.add(link)
                        title = entry.get("title", "")
                        img = get_image(entry)
                        send_message(title, source, img)
                        new_count += 1
                        time.sleep(3)
            except Exception as e:
                print("⚠️ خطأ:", e)
        if new_count == 0:
            print("⏸️ لا أخبار جديدة، التوقف مؤقتًا...")
        time.sleep(60)

if __name__ == "__main__":
    main()
