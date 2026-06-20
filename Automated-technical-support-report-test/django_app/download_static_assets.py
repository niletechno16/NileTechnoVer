"""
download_static_assets.py
=========================
شغّله مرة واحدة وقت الـ build (عن طريق build.sh).
بيحمّل:
  - خط Cairo (woff2) من Google Fonts  → static/fonts/cairo/ + static/css/cairo.css
  - Font Awesome 6.5                  → static/css/fontawesome.min.css + static/webfonts/
  - Chart.js 4.4                      → static/js/chart.umd.min.js
  - chartjs-plugin-datalabels 2.2     → static/js/chartjs-plugin-datalabels.min.js
"""

import os, re, sys, urllib.request, urllib.error, time

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

for d in ["fonts/cairo", "webfonts", "css", "js"]:
    os.makedirs(os.path.join(STATIC_DIR, d), exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

def fetch(url, retries=3, timeout=30):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            if i < retries - 1:
                time.sleep(2)
                continue
            raise e

def download(url, dest, label=""):
    name = label or os.path.basename(dest)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print(f"  ✓ موجود: {name}")
        return True
    print(f"  ↓ {name} ...", end="", flush=True)
    try:
        data = fetch(url)
        with open(dest, "wb") as f:
            f.write(data)
        print(f" ✓ ({len(data)//1024}KB)")
        return True
    except Exception as e:
        print(f" ✗ فشل: {e}")
        return False

errors = []

# ─── 1. Cairo ────────────────────────────────────────────────────────────────
print("\n[1/3] خط Cairo")
GOOGLE_CSS_URL = "https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap"
cairo_css_path = os.path.join(STATIC_DIR, "css", "cairo.css")

try:
    google_css = fetch(GOOGLE_CSS_URL).decode("utf-8")
    font_face_blocks = re.findall(r"@font-face\s*\{[^}]+\}", google_css, re.DOTALL)
    css_lines = []
    for block in font_face_blocks:
        m = re.search(r"url\((https://[^\)]+\.woff2[^\)]*)\)", block)
        if not m:
            continue
        woff2_url = m.group(1).strip("'\"")
        filename  = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", woff2_url.split("/")[-1].split("?")[0])
        if not filename.endswith(".woff2"):
            filename += ".woff2"
        dest = os.path.join(STATIC_DIR, "fonts", "cairo", filename)
        ok = download(woff2_url, dest, filename)
        if ok:
            local_block = re.sub(
                r"url\(https://[^\)]+\.woff2[^\)]*\)\s*format\('[^']+'\)",
                f"url('../fonts/cairo/{filename}') format('woff2')",
                block,
            )
            css_lines.append(local_block)
    if css_lines:
        with open(cairo_css_path, "w", encoding="utf-8") as f:
            f.write("\n".join(css_lines))
        print(f"  → cairo.css كُتب ({len(css_lines)} font-face blocks)")
    else:
        raise Exception("لا توجد font-face blocks")
except Exception as e:
    print(f"  ⚠ Google Fonts غير متاحة: {e}")
    print("  → fallback: Cairo من CDN مباشرة")
    with open(cairo_css_path, "w", encoding="utf-8") as f:
        f.write(
            "@import url('https://fonts.googleapis.com/css2"
            "?family=Cairo:wght@300;400;600;700;900&display=swap');\n"
        )
    errors.append("Cairo font")

# ─── 2. Font Awesome ─────────────────────────────────────────────────────────
print("\n[2/3] Font Awesome 6.5")
FA_BASE    = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0"
FA_CSS_URL = f"{FA_BASE}/css/all.min.css"
FA_CSS_DEST = os.path.join(STATIC_DIR, "css", "fontawesome.min.css")

ok = download(FA_CSS_URL, FA_CSS_DEST, "all.min.css")
if ok:
    fa_css = open(FA_CSS_DEST, encoding="utf-8").read()
    # استخرج أسماء الـ webfont files
    wf_files = list(dict.fromkeys(
        re.split(r"[?#\s]", wf)[0]
        for wf in re.findall(r"url\(\.\./webfonts/([^)]+)\)", fa_css)
    ))
    for wf in wf_files:
        download(f"{FA_BASE}/webfonts/{wf}", os.path.join(STATIC_DIR, "webfonts", wf), wf)
else:
    errors.append("Font Awesome")

# ─── 3. Chart.js ─────────────────────────────────────────────────────────────
print("\n[3/3] Chart.js & datalabels")

ok1 = download(
    "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js",
    os.path.join(STATIC_DIR, "js", "chart.umd.min.js"),
    "chart.umd.min.js"
)
ok2 = download(
    "https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js",
    os.path.join(STATIC_DIR, "js", "chartjs-plugin-datalabels.min.js"),
    "chartjs-plugin-datalabels.min.js"
)
if not ok1 or not ok2:
    errors.append("Chart.js")

# ─── Summary ─────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"⚠ انتهى مع مشاكل في: {', '.join(errors)}")
    sys.exit(1)
else:
    print("✅ كل الـ assets اتحملت بنجاح!")
