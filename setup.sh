#!/bin/sh
# Guided setup for Super3DX+ (Linux, Raspberry Pi, macOS): run ./setup.sh
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  exec python3 build.py wizard "$@"
fi
echo "Python 3 is not installed. On Ubuntu/Debian/Raspberry Pi OS: sudo apt install python3 python3-pip python3-venv"
exit 1
