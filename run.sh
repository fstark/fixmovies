#!/bin/bash
# Run the Samsung TV Media File Converter
# This script runs the application using system Python with PyGObject

cd "$(dirname "$0")"

# Use system Python3 to access system-installed PyGObject
# Set PYTHONPATH to include the virtual environment for langdetect
VENV_SITE_PACKAGES="$(pwd)/.venv/lib/python$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages"
export PYTHONPATH="$VENV_SITE_PACKAGES:$PYTHONPATH"

# Run with env -i to start with clean environment, keeping only essential variables
env -i \
    HOME="$HOME" \
    USER="$USER" \
    PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    DISPLAY="$DISPLAY" \
    XAUTHORITY="$XAUTHORITY" \
    PYTHONPATH="$PYTHONPATH" \
    LANG="$LANG" \
    python3 main.py
