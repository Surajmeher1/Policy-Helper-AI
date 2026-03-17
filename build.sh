#!/usr/bin/env bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Initialize database if needed
if [ ! -f instance/users.db ]; then
    flask db upgrade
fi
