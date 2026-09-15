#!/usr/bin/env bash
# Build script — runs collectstatic + migrate (used locally or by CI)
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
