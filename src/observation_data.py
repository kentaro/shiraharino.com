import json
from datetime import datetime

# 2026-05-21 is Day 1
relaunch_date = datetime(2026, 5, 21)
today = datetime.now()
day_number = (today - relaunch_date).days + 1

print(f"JST Day: {day_number}")
