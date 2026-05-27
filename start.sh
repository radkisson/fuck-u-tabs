#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ ! -d venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

pip install -q --upgrade pip
pip install -q -r requirements.txt
playwright install chromium --quiet

while true; do
    echo ""
    echo -e "\033[93mPaste your Ultimate Guitar link here (or type \"exit\" to quit):\033[0m"
    read -r -p "> " URL
    [ "$URL" = "exit" ] && break
    [ -z "$URL" ] && continue
    python app.py "$URL"
done

deactivate
