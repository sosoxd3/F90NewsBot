import feedparser
import requests
import time
import re
import json
from html import unescape
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8340084044:AAH4xDclN0yKECmpTFcnL5eshA4-qREHw4w")
CHAT_ID = os.getenv("CHAT_ID", "@f90newsnow")

# 📰 المصادر العربية
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

# نص الحقوق والروابط (يُعرض بخط صغير)
FOOTER = (
    "———\n"
    "📢 انضموا لنا لتَروا الأخبار لحظة بلحظة\n"
    "🌐 موقعنا الرسمي\n"
    "📲 تطبيق الأندرويد\n"
    "📡 قناة تيليجرام"
)

seen = set()

def clean_text(s):
    """تنظيف النص من الوسوم والعلامات الزائدة"""
    s = unescape(s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def get_image(entry):
    """محاولة استخراج صورة من الخبر"""
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

def make_inline_buttons(article_url):
    """إنشاء أزرار إيموجي فقط (الروابط مخفية داخلها)"""
    kb = {
        "inline_keyboard": [
            [
                {"text": "🔗 قراءة الخبر", "url": article_url},
                {"text": "🌐 موقعنا", "url": "https://e9dd-009-80041-a80rjkupq6lz-deployed-internal.easysite.ai/"},
                {"text": "📲 تطبيقنا", "url": "https://newoaks.s3.us-west-1.amazonaws.com/AutoDev/80041/d281064b-a82e-4fdf-bc19-d19cc4e0ccd4.apk"},
                {"text": "📡 القناة", "url": "https://t.me/f90newsnow"}
            ]
        ]
    }
    return json.dumps(kb, ensure_ascii=False)

def send_message(title, source, img=None, article_url=None):
    """إرسال الخبر إلى تيليجرام"""
    emphasized_title = f"🔴 <b>{clean_text(title)}</b>"

    caption = (
        f"{emphasized_title}\n"
        f"📡 <i>{clean_text(source)}</i>\n\n"
        f"<i>{FOOTER}</i>"
    )

    reply_markup = make_inline_buttons(article_url or "https://e9dd-009-80041-a80rjkupq6lz-deployed-internal.easysite.ai/")

    try:
        if img:
            # إرسال صورة مع النص
            res = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                data={
                    "chat_id": CHAT_ID,
                    "photo": img,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup
                },
                timeout=30
            )
        else:
            # إرسال نص فقط
            res = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={
                    "chat_id": CHAT_ID,
                    "text": caption,
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup,
                    "disable_web_page_preview": True
                },
                timeout=30
            )
        print("✅ تم نشر خبر:", clean_text(title)[:50])
    except Exception as e:
        print("⚠️ خطأ في الإرسال:", e)

def main():
    print("🚀 بدأ F90 News Bot العمل...")
    while True:
        new_count = 0
        for url in SOURCES:
            try:
                feed = feedparser.parse(url)
                source = feed.feed.get("title", "خبر عاجل")
                for entry in reversed(feed.entries):  # ترتيب من الأقدم للأحدث
                    link = entry.get("link")
                    if link and link not in seen:
                        seen.add(link)
                        title = entry.get("title", "")
                        img = get_image(entry)
                        send_message(title, source, img, link)
                        new_count += 1
                        time.sleep(3)
            except Exception as e:
                print("⚠️ خطأ:", e)
        if new_count == 0:
            print("⏸️ لا توجد أخبار جديدة الآن.")
        time.sleep(60)

if __name__ == "__main__":
    main()
