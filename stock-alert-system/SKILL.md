# Stock Alert System — Premium Skill

## Overview
Real-time stock and cryptocurrency price alerts via Telegram. Never miss a price target again.

**Price:** $19 standalone (or **$39 for the Bundle** with the Premium Model Router — save $9)

## Features
- ✅ Real-time price alerts (stocks, crypto, forex)
- ✅ Percentage change alerts (up/down 24h)
- ✅ Volume spike detection
- ✅ Telegram notifications (DM to @Wilson_hermesvision_bot)
- ✅ Persistent alert storage (survives restarts)
- ✅ Yahoo Finance API (no external API keys needed)
- ✅ License verification (offline)

## Installation

1. **Sponsor via GitHub:** [github.com/sponsors/Hermesplayground2](https://github.com/sponsors/Hermesplayground2)
2. **Email receipt** to: viktor@hermesplayground.com
3. **Receive license key:** `premium_stock_alerts.license`
4. **Install:**
   ```bash
   mkdir -p ~/.hermes/
   echo "YOUR-LICENSE-KEY" > ~/.hermes/premium_model_router.license
   
   # Copy skill to Hermes
   cp -r stock-alert-system/* ~/.hermes/skills/
   ```
5. **Restart Wilson bot**

## Usage

```
# Set price alerts
@jarvis set alert AAPL >150
@jarvis set alert BTC-USD <50000
@jarvis set alert NVDA >900

# Set percentage alerts
@jarvis set alert TSLA +5% in 24h
@jarvis set alert MARA -10% in 24h

# Set volume alerts
@jarvis set alert GME vol >50M

# List alerts
@jarvis list alerts

# Cancel alert
@jarvis cancel alert AAPL
```

## Supported Symbols
- **Stocks:** AAPL, TSLA, NVDA, GME, etc.
- **Crypto:** BTC-USD, ETH-USD, SOL-USD, etc.
- **Forex:** EURUSD=X, GBPJPY=X, etc.
- **ETFs:** SPY, QQQ, VXX, etc.

## Technical Details
- **Data source:** Yahoo Finance (no API key required)
- **Check interval:** 60 seconds (configurable)
- **Storage:** JSON file (portable, human-readable)
- **License:** Offline validation (no external calls)
- **Platform:** Works with Hermes/Jarvis on any OS

## Limitations
- Max 100 active alerts per user
- 60-second check interval (free API rate limits)
- Price precision depends on market data feed
- Telegram required for notifications (Signal coming soon)

## Support
- **Email:** viktor@hermesplayground.com
- **GitHub Issues:** github.com/Hermesplayground2/wilson-jarvis-api
- **Response time:** Within 48 hours (Pro tier)
