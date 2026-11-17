#!/usr/bin/env python3
"""
Stock Alert System for Hermes/Jarvis
=====================================

Real-time price alerts via Telegram. Never miss a price target again.

Commands:
  @jarvis set alert AAPL >150
  @jarvis set alert BTC-USD <50000
  @jarvis set alert AAPL +5% in 24h
  @jarvis set alert TSLA vol >10M
  @jarvis list alerts
  @jarvis cancel alert AAPL

Price: $19 (one-time)
Requires: hermes>=4.0 + valid license

Built on Yahoo Finance API with Telegram notifications.
"""

import json
import time
import re
import sys
import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

# --- License Check ---

LICENSE_FILE = Path.home() / 'AppData' / 'Local' / 'hermes' / 'premium_model_router.license'

VALID_LICENSES = [
    'PMR-LIVE-2026-0001',
    'PMR-LIVE-2026-0002',
    'PMR-LIVE-2026-0003',
    'ALERT-BETA-2026-0001',
]

def validate_license() -> bool:
    """Check if premium license is valid."""
    if LICENSE_FILE.exists():
        content = LICENSE_FILE.read_text().strip()
        return content != '' and content in VALID_LICENSES
    return False


# --- Configuration ---

ALERTS_FILE = Path.home() / 'AppData' / 'Local' / 'hermes' / 'stock_alerts.json'
CHECK_INTERVAL = 60  # seconds

# Yahoo Finance API config
CHART_API = 'https://query1.finance.yahoo.com/v8/finance/chart'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# --- Data Models ---

@dataclass
class Alert:
    symbol: str
    condition_type: str  # 'price_above', 'price_below', 'pct_change', 'volume'
    threshold: float
    direction: str = 'above'  # 'above' or 'below'
    timeframe: str = 'realtime'  # 'realtime', '24h'
    created_at: str = ''
    triggered: bool = False
    last_triggered: str = ''
    trigger_count: int = 0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__annotations__})


# --- Alert Storage ---

def load_alerts() -> List[Alert]:
    """Load alerts from storage."""
    try:
        if ALERTS_FILE.exists():
            data = json.loads(ALERTS_FILE.read_text())
            return [Alert.from_dict(a) for a in data.get('alerts', [])]
    except Exception:
        pass
    return []


def save_alerts(alerts: List[Alert]) -> None:
    """Save alerts to storage."""
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {'alerts': [a.to_dict() for a in alerts]}
    ALERTS_FILE.write_text(json.dumps(data, indent=2))


# --- Yahoo Finance API ---

def get_quote(symbol: str) -> Dict[str, Any]:
    """Get current quote for a symbol using Yahoo Finance v8 chart API."""
    import urllib.request
    
    try:
        # Use v8 chart API (still works without auth)
        url = f"{CHART_API}/{symbol}?range=1d&interval=1m&includePrePost=true"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            result = data.get('chart', {}).get('result', [])
            if result and result[0]:
                r = result[0]
                meta = r.get('meta', {})
                quotes = r.get('indicators', {}).get('quote', [{}])
                q = quotes[0] if quotes else {}
                
                # Get latest non-null close price
                closes = [c for c in q.get('close', []) if c is not None]
                highs = [c for c in q.get('high', []) if c is not None]
                lows = [c for c in q.get('low', []) if c is not None]
                
                current_price = closes[-1] if closes else meta.get('previousClose', 0)
                previous_price = closes[0] if len(closes) > 1 else meta.get('previousClose', current_price)
                
                change_pct = ((current_price - previous_price) / previous_price * 100) if previous_price else 0
                
                # Get volume
                volumes = q.get('volume', [])
                avg_volume = sum(v for v in volumes if v is not None) / len([v for v in volumes if v is not None]) if volumes else 0
                
                return {
                    'symbol': meta.get('symbol', symbol),
                    'regularMarketPrice': current_price,
                    'regularMarketChangePercent': round(change_pct, 2),
                    'regularMarketVolume': int(avg_volume) if avg_volume else 0,
                    'regularMarketPreviousClose': previous_price,
                    'regularMarketTime': meta.get('regularMarketTime', 0),
                    'currency': meta.get('currency', 'USD'),
                }
    except Exception as e:
        return {'error': str(e)}
    
    return {'error': 'No data returned'}


def get_chart(symbol: str, range_days: int = 30) -> Optional[Dict]:
    """Get historical chart data."""
    import urllib.request
    
    range_str = f'{range_days}d' if range_days <= 30 else '5d'
    url = f"{CHART_API}/{symbol}?range={range_str}&interval=1d&includePrePost=true"
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            result = data.get('chart', {}).get('result', [])
            if result:
                return result[0]
    except Exception:
        pass
    
    return None


def calculate_pct_change(symbol: str, timeframe: str = '24h') -> Optional[float]:
    """Calculate percentage change for a symbol."""
    chart = get_chart(symbol, 30 if timeframe == '24h' else 5)
    if not chart:
        return None
    
    closes = chart.get('indicators', {}).get('quote', [{}])[0].get('close', [])
    if len(closes) < 2:
        return None
    
    # Filter out None values
    closes = [c for c in closes if c is not None]
    if len(closes) < 2:
        return None
    
    if timeframe == '24h':
        # Compare last two closes
        if len(closes) >= 2:
            change = ((closes[-1] - closes[-2]) / closes[-2]) * 100
            return round(change, 2)
    elif timeframe == '5d':
        change = ((closes[-1] - closes[0]) / closes[0]) * 100
        return round(change, 2)
    
    return None


# --- Alert Checking ---

def check_alert(alert: Alert) -> bool:
    """Check if an alert condition is met. Returns True if triggered."""
    quote = get_quote(alert.symbol)
    
    if 'error' in quote:
        return False
    
    # Get current values
    current_price = quote.get('regularMarketPrice', 0)
    volume = quote.get('regularMarketVolume', 0)
    change_pct = quote.get('regularMarketChangePercent', 0)
    
    triggered = False
    
    if alert.condition_type == 'price_above':
        if current_price >= alert.threshold:
            triggered = True
    elif alert.condition_type == 'price_below':
        if current_price <= alert.threshold:
            triggered = True
    elif alert.condition_type == 'pct_change':
        if change_pct >= alert.threshold:
            triggered = True
    elif alert.condition_type == 'volume':
        if volume >= alert.threshold:
            triggered = True
    
    return triggered


def format_alert_message(alert: Alert, quote_data: Dict) -> str:
    """Format an alert notification message."""
    current_price = quote_data.get('regularMarketPrice', 'N/A')
    change = quote_data.get('regularMarketChangePercent', 0)
    change_str = f"📈 {change:+.2f}%" if change >= 0 else f"📉 {change:.2f}%"
    
    symbol = alert.symbol
    condition_desc = {
        'price_above': f"above ${alert.threshold}",
        'price_below': f"below ${alert.threshold}",
        'pct_change': f"up {alert.threshold}% today",
        'volume': f"volume > {int(alert.threshold):,}"
    }.get(alert.condition_type, alert.condition_type)
    
    return (
        f"🚨 ALERT TRIGGERED\n"
        f"{symbol} is now ${current_price} ({change_str})\n\n"
        f"Condition: {condition_desc}\n"
        f"At: {datetime.now().strftime('%H:%M:%S UTC')}"
    )


# --- Command Handlers ---

def handle_set_alert(user_input: str) -> str:
    """Parse and create an alert from user input."""
    # Parse: "set alert AAPL >150" or "set alert BTC-USD <50000"
    
    # Extract symbol and conditions
    symbols = re.findall(r'\b([A-Z]{1,5}(?:-[A-Z]{1,3})?)\b', user_input)
    if not symbols:
        return "❌ Please include a symbol. Example: `set alert AAPL >150`"
    
    symbol = symbols[0].upper()
    alerts = load_alerts()
    
    # Parse price condition
    price_match = re.search(r'([<>])\s*(\d+(?:\.\d+)?)', user_input)
    if price_match:
        direction = price_match.group(1)
        threshold = float(price_match.group(2))
        condition_type = 'price_above' if direction == '>' else 'price_below'
        
        # Check for timeframe modifier
        if '24h' in user_input or 'today' in user_input.lower():
            timeframe = '24h'
            # Use percentage change instead
            pct = calculate_pct_change(symbol, '24h')
            if pct is not None:
                return f"📊 {symbol} is at {pct:+.2f}% today"
            return f"❌ Could not fetch data for {symbol}"
        else:
            timeframe = 'realtime'
        
        alert = Alert(
            symbol=symbol,
            condition_type=condition_type,
            threshold=threshold,
            direction=direction,
            timeframe=timeframe
        )
        alerts.append(alert)
        save_alerts(alerts)
        
        quote = get_quote(symbol)
        current = quote.get('regularMarketPrice', 'N/A')
        
        return (
            f"✅ Alert set!\n\n"
            f"**{symbol}**\n"
            f"Condition: Price {direction} ${threshold}\n"
            f"Current: ${current}\n"
            f"Checking every {CHECK_INTERVAL}s\n"
            f"ID: #{len(alerts)}"
        )
    
    # Parse percentage change
    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%.*24h', user_input.replace('+', ''))
    if pct_match:
        threshold = float(pct_match.group(1))
        alert = Alert(
            symbol=symbol,
            condition_type='pct_change',
            threshold=threshold,
            timeframe='24h'
        )
        alerts.append(alert)
        save_alerts(alerts)
        return f"✅ Alert set for {symbol} up {threshold}% in 24h"
    
    # Parse volume
    vol_match = re.search(r'vol.*?\d+(?:\.\d+)?[kKmM]?', user_input.replace('>', ''))
    if vol_match:
        vol_str = vol_match.group(0)
        # Parse K/M suffixes
        num_match = re.search(r'(\d+(?:\.\d+)?)([kKmM]?)', vol_str)
        if num_match:
            num = float(num_match.group(1))
            suffix = num_match.group(2).upper()
            if suffix == 'K':
                threshold = num * 1000
            elif suffix == 'M':
                threshold = num * 1000000
            else:
                threshold = num
            
            alert = Alert(
                symbol=symbol,
                condition_type='volume',
                threshold=threshold,
                timeframe='realtime'
            )
            alerts.append(alert)
            save_alerts(alerts)
            return f"✅ Alert set for {symbol} volume > {int(threshold):,}"
    
    return (
        "❌ Could not parse alert.\n\n"
        "Examples:\n"
        "- `set alert AAPL >150`\n"
        "- `set alert BTC-USD <50000`\n"
        "- `set alert AAPL +5% in 24h`\n"
        "- `set alert TSLA vol >10M`"
    )


def handle_list_alerts() -> str:
    """List all active alerts."""
    alerts = load_alerts()
    active = [a for a in alerts if not a.triggered]
    
    if not active:
        return "📭 No active alerts. Set one with: `set alert AAPL >150`"
    
    result = "📋 Active Alerts:\n\n"
    for i, a in enumerate(active, 1):
        condition = {
            'price_above': f"Price > ${a.threshold}",
            'price_below': f"Price < ${a.threshold}",
            'pct_change': f"Up {a.threshold}% today",
            'volume': f"Volume > {int(a.threshold):,}"
        }.get(a.condition_type, a.condition_type)
        
        quote = get_quote(a.symbol)
        current = quote.get('regularMarketPrice', '?')
        change = quote.get('regularMarketChangePercent', 0)
        change_str = f"📈{change:+.2f}%" if change >= 0 else f"📉{change:.2f}%"
        
        result += (
            f"{i}. {a.symbol} — {condition}\n"
            f"   Current: ${current} ({change_str})\n"
            f"   Created: {a.created_at[:10]}\n\n"
        )
    
    return result


def handle_cancel_alert(symbol: str) -> str:
    """Cancel an alert by symbol."""
    alerts = load_alerts()
    original_len = len(alerts)
    
    # Filter out alerts for this symbol
    alerts = [a for a in alerts if a.symbol != symbol.upper()]
    
    if len(alerts) < original_len:
        save_alerts(alerts)
        return f"✅ Cancelled alerts for {symbol.upper()}"
    else:
        return f"❌ No alerts found for {symbol.upper()}"


# --- Main Check Loop ---

def monitor_alerts(send_notification_callback) -> str:
    """Check all alerts and send notifications for triggered ones."""
    alerts = load_alerts()
    active = [a for a in alerts if not a.triggered]
    
    notifications = []
    
    for alert in active:
        if check_alert(alert):
            quote = get_quote(alert.symbol)
            message = format_alert_message(alert, quote)
            send_notification_callback(message)
            
            alert.triggered = True
            alert.last_triggered = datetime.now().isoformat()
            alert.trigger_count += 1
            save_alerts(alerts)
            
            notifications.append(f"🔔 {alert.symbol}: {message}")
    
    if not notifications:
        return "All checks passed. No alerts triggered."
    
    return f"{len(notifications)} alert(s) triggered"


# --- CLI ---

if __name__ == '__main__':
    if not validate_license():
        print("ERROR: License not found. Contact viktor@hermesplayground.com")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Stock Alert System v1.0")
        print("Commands: set-alert, list-alerts, cancel-alert, check, status, test")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'set-alert':
        # args: symbol, condition_type, threshold
        if len(sys.argv) >= 5:
            _, _, symbol, cond, threshold = sys.argv[:5]
            alert = Alert(
                symbol=symbol.upper(),
                condition_type=cond,
                threshold=float(threshold),
            )
            alerts = load_alerts()
            alerts.append(alert)
            save_alerts(alerts)
            print(f"✓ Alert set: {symbol.upper()} {cond} {threshold}")
        else:
            print("Usage: python skill.py set-alert <SYMBOL> <condition> <threshold>")
            print("Conditions: price_above, price_below, pct_change, volume")
    
    elif cmd == 'list-alerts':
        alerts = load_alerts()
        for a in alerts:
            print(f"{a.symbol}: {a.condition_type} {a.threshold} (triggered={a.triggered})")
    
    elif cmd == 'cancel-alert':
        symbol = sys.argv[2]
        alerts = load_alerts()
        alerts = [a for a in alerts if a.symbol != symbol.upper()]
        save_alerts(alerts)
        print(f"✓ Cancelled alerts for {symbol.upper()}")
    
    elif cmd == 'check':
        # Single check cycle
        alerts = load_alerts()
        print(f"Checking {len(alerts)} alerts...")
        for alert in alerts:
            if not alert.triggered:
                quote = get_quote(alert.symbol)
                current = quote.get('regularMarketPrice', 'N/A')
                print(f"  {alert.symbol}: ${current}")
    
    elif cmd == 'status':
        print(json.dumps({
            'alerts_file': str(ALERTS_FILE),
            'check_interval': CHECK_INTERVAL,
            'license_valid': validate_license(),
            'api_base': API_BASE
        }, indent=2))
    
    elif cmd == 'test':
        # Test API connectivity
        r = get_quote('AAPL')
        if 'error' in r:
            print(f"✗ API error: {r['error']}")
        else:
            print(f"✓ AAPL: ${r.get('regularMarketPrice')}")
    
    elif cmd.startswith('handle-'):
        # Direct handler calls
        if cmd == 'handle-set-alert':
            print(handle_set_alert(sys.argv[2]))
        elif cmd == 'handle-list-alerts':
            print(handle_list_alerts())
        elif cmd == 'handle-cancel-alert':
            print(handle_cancel_alert(sys.argv[2]))
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
