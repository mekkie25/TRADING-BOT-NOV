# trading-engine/knowledge/news.py
import json
from datetime import datetime, timedelta
from pathlib import Path

CURRENT_FOLDER = Path(__file__).resolve().parent 
ENGINE_FOLDER = CURRENT_FOLDER.parent 
CALENDAR_PATH = ENGINE_FOLDER / "news_feed" / "news" / "last_run"

def load_news_events():
    try:
        if not CALENDAR_PATH.exists():
            return []
        json_files = list(CALENDAR_PATH.glob("*.json"))
        if not json_files:
            return []
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        return []

def is_news_blackout(current_time_sast: datetime, pair: str):
    events = load_news_events()
    if not events:
        return {"blocked": False}
        
    pair_currencies = [pair[:3], pair[3:6]] 
    
    for event in events:
        impact = str(event.get('impact', '')).strip().lower()
        currency = str(event.get('currency', '')).strip().upper()
        
        if impact not in ['red', 'high', '3'] or currency not in pair_currencies:
            continue
            
        event_date_str = event.get('date', '')
        event_time_str = event.get('time', '00:00')
        
        # Skip events that are all day (we don't know the exact time)
        if event_date_str == 'All Day' or event_time_str == 'All Day':
            continue
            
        try:
            # The date is DD/MM/YYYY and time is HH:MM
            full_time_str = f"{event_date_str} {event_time_str}"
            raw_event_time = datetime.strptime(full_time_str, "%d/%m/%Y %H:%M")
            
            # Karachi is UTC+5, South Africa is UTC+2. So we subtract 3 hours.
            event_time_sast = raw_event_time - timedelta(hours=3)
            
        except ValueError:
            continue
            
        window_start = event_time_sast - timedelta(minutes=30)
        window_end = event_time_sast + timedelta(minutes=30)
        
        if "FOMC" in str(event.get('event', '')):
            window_end = event_time_sast + timedelta(minutes=60)
        
        if window_start <= current_time_sast <= window_end:
            return {
                "blocked": True,
                "event": event.get('event', 'Unknown Event'),
                "time": event_time_sast.strftime("%H:%M"),
                "reason": f"News blackout: {event.get('event')} affecting {currency}"
            }
    
    return {"blocked": False}