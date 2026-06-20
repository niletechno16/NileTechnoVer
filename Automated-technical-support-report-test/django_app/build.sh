#!/usr/bin/env bash
set -e

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Downloading static assets (fonts, icons, charts)..."
python download_static_assets.py

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Build complete."
