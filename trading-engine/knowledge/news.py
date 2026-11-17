"""
Module 4: News & Economic Calendar
Depends on: common.py only (and the news_feed scraper output).

Purpose: Prevent the bot from trading into high-impact news events that cause spread spikes and 
whipsaws, which violate our SMC entry logic.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# ==========================================
# 1. CONFIGURATION & DATA STRUCTURES
# ==========================================

@dataclass
class NewsConfig:
    default_buffer_before: int = 30  # minutes
    default_buffer_after: int = 30   # minutes
    fomc_buffer_after: int = 60      # FOMC press conferences run long
    blackout_impacts: tuple = ('red', 'high', '3')
    
    # Mapping symbols to their constituent currencies (fixes the pair[3:6] bug)
    # This handles Forex, Metals, and Indices.
    pair_currencies: Dict[str, List[str]] = None

    def __post_init__(self):
        if self.pair_currencies is None:
            self.pair_currencies = {
                # Majors
                'EURUSD': ['EUR', 'USD'], 'GBPUSD': ['GBP', 'USD'],
                'USDJPY': ['USD', 'JPY'], 'USDCHF': ['USD', 'CHF'],
                'USDCAD': ['USD', 'CAD'], 'AUDUSD': ['AUD', 'USD'],
                'NZDUSD': ['NZD', 'USD'],
                # Crosses
                'EURGBP': ['EUR', 'GBP'], 'EURJPY': ['EUR', 'JPY'],
                'GBPJPY': ['GBP', 'JPY'],
                # Commodities
                'XAUUSD': ['XAU', 'USD'], 'XAGUSD': ['XAG', 'USD'],
                # Exotics (SA context)
                'USDZAR': ['USD', 'ZAR'], 'EURZAR': ['EUR', 'ZAR'],
                'GBPZAR': ['GBP', 'ZAR'], 'XAUZAR': ['XAU', 'ZAR']
            }

@dataclass
class NewsBlackoutResult:
    blocked: bool
    event_name: Optional[str] = None
    event_time_sast: Optional[str] = None
    reason: Optional[str] = None
    impact: Optional[str] = None
    currency: Optional[str] = None

# ==========================================
# 2. CORE LOGIC
# ==========================================

# Assuming file is located at: trading-engine/knowledge/news.py
CURRENT_FOLDER = Path(__file__).resolve().parent 
ENGINE_FOLDER = CURRENT_FOLDER.parent 
CALENDAR_PATH = ENGINE_FOLDER / "news_feed" / "news" / "last_run"

def load_news_events() -> List[Dict[str, Any]]:
    """Loads the latest JSON file from the scraper."""
    try:
        if not CALENDAR_PATH.exists():
            return []
        json_files = list(CALENDAR_PATH.glob("*.json"))
        if not json_files:
            return []
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def _parse_event_time(event: dict) -> Optional[datetime]:
    """Converts the scraper's DD/MM/YYYY HH:MM format (Karachi time) to SAST."""
    event_date_str = event.get('date', '')
    event_time_str = event.get('time', '00:00')
    
    if event_date_str == 'All Day' or event_time_str == 'All Day':
        return None
        
    try:
        full_time_str = f"{event_date_str} {event_time_str}"
        raw_event_time = datetime.strptime(full_time_str, "%d/%m/%Y %H:%M")
        
        # Karachi is UTC+5, South Africa is UTC+2. So we subtract 3 hours.
        return raw_event_time - timedelta(hours=3)
    except ValueError:
        return None

def is_news_blackout(current_time_sast: datetime, pair: str, config: NewsConfig = NewsConfig()) -> NewsBlackoutResult:
    """
    Checks if the given pair is currently in a news blackout window.
    """
    events = load_news_events()
    if not events:
        return NewsBlackoutResult(blocked=False)
        
    # Get currencies to check
    pair = pair.upper().replace("/", "").replace("_", "")
    currencies_to_check = config.pair_currencies.get(pair, [pair[:3], pair[3:]])
    
    for event in events:
        impact = str(event.get('impact', '')).strip().lower()
        currency = str(event.get('currency', '')).strip().upper()
        
        if impact not in config.blackout_impacts or currency not in currencies_to_check:
            continue
            
        event_time_sast = _parse_event_time(event)
        if not event_time_sast:
            continue
            
        window_start = event_time_sast - timedelta(minutes=config.default_buffer_before)
        window_end = event_time_sast + timedelta(minutes=config.default_buffer_after)
        
        # FOMC press conferences need a longer buffer
        if "FOMC" in str(event.get('event', '')).upper():
            window_end = event_time_sast + timedelta(minutes=config.fomc_buffer_after)
        
        if window_start <= current_time_sast <= window_end:
            return NewsBlackoutResult(
                blocked=True,
                event_name=event.get('event', 'Unknown Event'),
                event_time_sast=event_time_sast.strftime("%H:%M"),
                impact=impact,
                currency=currency,
                reason=f"News blackout: {event.get('event')} affecting {currency}"
            )
    
    return NewsBlackoutResult(blocked=False)

# ==========================================
# 3. ANALYZE WRAPPER (For Consistency)
# ==========================================

def analyze(current_time_sast: datetime, pair: str, config: NewsConfig = NewsConfig()) -> NewsBlackoutResult:
    """Main entry point to be called by strategies."""
    return is_news_blackout(current_time_sast, pair, config)