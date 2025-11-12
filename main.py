#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F90 News Telegram Bot
- Fetches Arabic news from multiple RSS sources
- Posts immediately to Telegram channel
- Uses article image if available; otherwise sends small F90 logo
- Appends credits & channel link
Run: python main.py
"""

import os
import time
import json
import re
import requests
import feedparser
from html import unescape

# ============ CONFIG ============
# Put your bot token here (or set env BOT_TOKEN)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8340084044:AAH4xDclN0yKECmpTFcnL5eshA4-qREHw4w")
# Telegram channel/user to post to (e.g., @f90newsnow)
CHAT_ID = os.getenv("CHAT_ID", "@f90newsnow")

# Polling interval (seconds). 20 = near instant without hammering RSS
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "20"))

# Small logo path (used when no image found)
LOGO_PATH = os.getenv("LOGO_PATH", os.path.join("assets", "logo.png"))

# Credits footer (always appended)
CREDITS = "———\n© F90 News | جميع الحقوق محفوظة\n📢 تابعنا على @f90newsnow"

# RSS sources (Arabic + sports + tech + business + Palestine)
SOURCES = [
    # General / Breaking
    "https://www.aljazeera.net/xml/rss/all.xml",
    "https://www.alarabiya.net/.mrss/ar.xml",
    "https://www.skynewsarabia.com/web/rss",
    "https://arabic.rt.com/rss/",
    "https://www.bbc.com/arabic/index.xml",
    "https://arabic.cnn.com/rss",
    # Palestine / local
    "https://shehabnews.com/ar/rss.xml",
    "https://qudsn.co/feed",
    "https://www.maannews.net/rss/ar.xml",
    # Sports
    "https://www.beinsports.com/ar/rss",
    "https://www.alarabiya.net/sport/.mrss/ar.xml",
    "https://www.skynewsarabia.com/web/rss/sports",
    # Business + Tech + Variety
    "https://www.asharqbusiness.com/ar/rss",
    "https://aitnews.com/feed/",
    "https://www.tech-wd.com/wd/feed/",
    "https://www.skynewsarabia.com/web/rss/varieties"
]

SEEN_FILE = "seen.json"
# =================================

def load_seen():
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_seen(seen_set):
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(list(seen_set), f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def clean_text(s):
    if not s:
        return ""
    s = unescape(s)
    # remove HTML tags
    s = re.sub(r"<[^>]+>", "", s)
    # compress whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_image(entry):
    # Try common fields
    for key in ("media_content", "media_thumbnail"):
        val = entry.get(key)
        if isinstance(val, list) and val:
            url = val[0].get("url")
            if url:
                return url
    # enclosure
    enc = entry.get("enclosures") or entry.get("enclosure")
    if isinstance(enc, list) and enc:
        url = enc[0].get("href") or enc[0].get("url")
        if url: return url
    if isinstance(enc, dict):
        url = enc.get("href") or enc.get("url")
        if url: return url
    # content HTML
    for key in ("summary", "description", "content"):
        html = entry.get(key)
        if isinstance(html, list) and html:
            html = html[0].get("value")
        if isinstance(html, str):
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html)
            if m:
                return m.group(1)
    return None

def telegram_send_photo(photo_url_or_path, caption):
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = None
    data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        if photo_url_or_path and re.match(r"^https?://", str(photo_url_or_path)):
            data["photo"] = photo_url_or_path
            r = requests.post(api, data=data, timeout=30)
        else:
            # send local file (logo)
            with open(photo_url_or_path, "rb") as f:
                files = {"photo": f}
                r = requests.post(api, data=data, files=files, timeout=30)
        if r.status_code != 200:
            print("sendPhoto failed:", r.text)
        else:
            print("✅ Published with photo")
    except Exception as e:
        print("sendPhoto error:", e)

def telegram_send_text(text):
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        r = requests.post(api, data=data, timeout=30)
        if r.status_code != 200:
            print("sendMessage failed:", r.text)
        else:
            print("✅ Published as text")
    except Exception as e:
        print("sendMessage error:", e)

def build_caption(title, source, link):
    title = clean_text(title)
    source = clean_text(source)
    cap = f"📰 <b>{title}</b>\n📡 المصدر: {source}\n🔗 {link}\n\n{CREDITS}"
    # Telegram caption limit ~1024 chars
    if len(cap) > 1000:
        cap = cap[:980] + "…\n\n" + CREDITS
    return cap

def main():
    if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE":
        raise SystemExit("❌ ضع توكن البوت في BOT_TOKEN أو كمتغير بيئة BOT_TOKEN")

    seen = load_seen()
    print("🚀 F90 News Bot started. Posting to:", CHAT_ID)
    print("🕒 Poll interval:", POLL_SECONDS, "sec")
    while True:
        new_posts = 0
        for url in SOURCES:
            try:
                feed = feedparser.parse(url)
                source_name = feed.feed.get("title", "News")
                for entry in feed.entries:
                    link = entry.get("link") or entry.get("id")
                    title = entry.get("title") or ""
                    if not link or not title:
                        continue
                    if link in seen:
                        continue

                    # caption
                    caption = build_caption(title, source_name, link)

                    # image
                    img = extract_image(entry)
                    if img:
                        telegram_send_photo(img, caption)
                    else:
                        # fallback to small logo
                        if os.path.exists(LOGO_PATH):
                            telegram_send_photo(LOGO_PATH, caption)
                        else:
                            telegram_send_text(caption)

                    seen.add(link)
                    new_posts += 1
                    time.sleep(1.5)  # polite delay between posts
            except Exception as e:
                print(f"⚠️ Error parsing {url}: {e}")
        if new_posts:
            save_seen(seen)
        print("🔄 cycle done. new posts:", new_posts)
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
