#!/bin/bash
# Pepper Bowl Daily Trend Reporter — scheduled runner
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
cd /Users/murali/kodi_innovations/pinterest_manager
echo "--- $(date) ---" >> run.log
git pull origin main >> run.log 2>&1
/usr/bin/python3 daily_trends.py >> run.log 2>&1
