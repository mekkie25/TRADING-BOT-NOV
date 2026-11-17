# trading-engine/knowledge/sessions.py
from datetime import datetime, time

def get_session_sast(current_time_sast: datetime):
    """
    Takes the current SAST time (South Africa Standard Time, UTC+2).
    Returns the session name, killzone status, and bot action rules.
    """
    t = current_time_sast.time()
    month = current_time_sast.month
    
    # Determine if we are in the "Summer" (Apr-Oct) or "Winter" (Nov-Mar) period
    is_summer = 4 <= month <= 10

    # ==========================================
    # 1. ASIAN SESSION & DEAD ZONE
    # ==========================================
    if time(2, 0) <= t < time(11, 0):
        # Asian Dead Zone (04:00 to 06:00 SAST) - Lowest volume
        if time(4, 0) <= t < time(6, 0):
            return {
                "session": "ASIAN_DEAD_ZONE",
                "killzone": False,
                "strategy_type": "NO_TRADING",
                "warning": "Lowest volume of the day. Do not trade."
            }
        # General Asian Session
        return {
            "session": "ASIAN",
            "killzone": False,
            "strategy_type": "Range / Mean Reversion",
            "warning": "Track High/Low for London sweeps. No breakouts."
        }

    # ==========================================
    # 2. LONDON SESSION & KILL ZONES (2 Hours)
    # ==========================================
    if is_summer:
        # Summer London (Apr-Oct)
        if time(9, 0) <= t < time(11, 0):
            return {
                "session": "LONDON_KILLZONE",
                "killzone": True,
                "strategy_type": "Liquidity Sweep / Breakout",
                "warning": "A++ Window. Hunt Asian High/Low sweeps."
            }
        elif time(9, 0) <= t < time(18, 0):
            return {"session": "LONDON", "killzone": False, "strategy_type": "Trend Continuation"}
    else:
        # Winter London (Nov-Mar)
        if time(10, 0) <= t < time(12, 0):
            return {
                "session": "LONDON_KILLZONE",
                "killzone": True,
                "strategy_type": "Liquidity Sweep / Breakout",
                "warning": "A++ Window. Hunt Asian High/Low sweeps."
            }
        elif time(10, 0) <= t < time(19, 0):
            return {"session": "LONDON", "killzone": False, "strategy_type": "Trend Continuation"}

    # ==========================================
    # 3. NEW YORK & OVERLAP KILL ZONES (2 Hours)
    # ==========================================
    if is_summer:
        # Summer NY (Apr-Oct)
        if time(14, 0) <= t < time(16, 0):
            return {
                "session": "NY_AM_KILLZONE",
                "killzone": True,
                "strategy_type": "High Volatility Breakout",
                "warning": "A++ Window. London/NY overlap. US Data hits at 14:30."
            }
        elif time(14, 0) <= t < time(23, 0):
            return {"session": "NEW_YORK", "killzone": False, "strategy_type": "Continuation / Reversal"}
            
    else:
        # Winter NY (Nov-Mar)
        if time(15, 0) <= t < time(17, 0):
            return {
                "session": "NY_AM_KILLZONE",
                "killzone": True,
                "strategy_type": "High Volatility Breakout",
                "warning": "A++ Window. London/NY overlap. US Data hits at 15:30."
            }
        elif time(15, 0) <= t < time(0, 0):
            return {"session": "NEW_YORK", "killzone": False, "strategy_type": "Continuation / Reversal"}

    # ==========================================
    # 4. DEAD ZONES (NO TRADING)
    # ==========================================
    # NY Lunch Dead Zone (19:00 to 20:00 SAST)
    if time(19, 0) <= t < time(20, 0):
        return {
            "session": "NY_LUNCH_DEAD_ZONE",
            "killzone": False,
            "strategy_type": "NO_TRADING",
            "warning": "Spreads widen. Do not enter new trades."
        }

    # Late NY / Rollover Dead Zone (22:00 to 02:00 SAST)
    if t >= time(22, 0) or t < time(2, 0):
        return {
            "session": "LATE_DEAD_ZONE",
            "killzone": False,
            "strategy_type": "NO_TRADING",
            "warning": "Rollover period. Dangerous spreads. Do not trade."
        }

    # Fallback for any unhandled minutes (e.g., 20:00 - 22:00 SAST)
    return {
        "session": "TRANSITION",
        "killzone": False,
        "strategy_type": "NO_TRADING",
        "warning": "Waiting for next session."
    }

def get_asian_range(asian_bars):
    """
    Takes all the candles from the Asian session (02:00 to 11:00 SAST)
    and returns the High and Low. London often sweeps these levels.
    """
    if not asian_bars:
        return None
        
    asian_high = max([bar['high'] for bar in asian_bars])
    asian_low = min([bar['low'] for bar in asian_bars])
    
    return {
        "asian_high": asian_high,
        "asian_low": asian_low,
        "midpoint": (asian_high + asian_low) / 2
    }