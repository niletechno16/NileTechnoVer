"""
keep_alive.py
=============
يمنع Render من تنويم السيرفر بعمل ping لنفسه كل 10 دقايق.
بيشتغل في background thread منفصل تلقائياً مع بداية Django.

متغير البيئة المطلوب على Render:
    SELF_URL = https://your-app-name.onrender.com
"""

import threading
import time
import os
import urllib.request
import urllib.error


PING_INTERVAL = 10 * 60      # 10 دقايق بالثواني
PING_TIMEOUT  = 15           # ثواني انتظار قبل timeout
_started      = False
_lock         = threading.Lock()


def _ping_loop():
    url = os.getenv("SELF_URL", "").rstrip("/")
    if not url:
        print("[keep_alive] SELF_URL غير موجود — الـ keep-alive مش شغال", flush=True)
        return

    ping_url = f"{url}/keep-alive/ping/"
    print(f"[keep_alive] شغال ✓  — بيعمل ping كل {PING_INTERVAL // 60} دقايق على: {ping_url}", flush=True)

    while True:
        time.sleep(PING_INTERVAL)
        try:
            req = urllib.request.urlopen(ping_url, timeout=PING_TIMEOUT)
            print(f"[keep_alive] ping OK — status {req.status}", flush=True)
        except urllib.error.URLError as e:
            print(f"[keep_alive] ping فشل: {e.reason}", flush=True)
        except Exception as e:
            print(f"[keep_alive] ping error: {e}", flush=True)


def start():
    """بيشغّل الـ background thread مرة واحدة بس."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    t = threading.Thread(target=_ping_loop, name="keep_alive", daemon=True)
    t.start()
