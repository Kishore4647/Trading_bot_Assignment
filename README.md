# Binance Futures Testnet Trading Bot

A lightweight Python CLI application for placing orders on Binance Futures Testnet (USDT-M).

---

#Note: Please Create a .env file and get your API and Secert Keys and set environment Variables. 

## Features

| Feature | Details |
|---|---|
| Order types | MARKET, LIMIT, STOP_MARKET (bonus) |
| Sides | BUY and SELL |
| CLI framework | Click — clean flags, `--help` on every command |
| Credentials | `.env` file or environment variables |
| Logging | Structured file + console logging (date-stamped log files) |
| Validation | Dedicated validators module — catches bad input before hitting the API |
| Error handling | Network errors, API errors, and input errors are all caught and reported clearly |
| Dry-run mode | `--dry-run` prints request summary without submitting |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (auth, signing, HTTP)
│   ├── orders.py          # Order placement logic + OrderResult dataclass
│   ├── validators.py      # Input validation helpers
│   └── logging_config.py  # File + console logger setup
├── cli.py                 # CLI entry point (Click)
├── logs/                  # Auto-created; log files written here
├── .env.example           # Copy to .env and fill in credentials
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet Credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com) and log in with GitHub.
2. Go to **API Key** tab and generate a new key pair.
3. Copy your API Key and Secret.

### 2. Clone / Unzip and Install Dependencies

```bash
# Inside the trading_bot/ directory
pip install -r requirements.txt
```

### 3. Configure Credentials

```bash
cp .env.example .env
# Edit .env and fill in your API key and secret
```

Or pass them as flags / environment variables directly:

```bash
export BINANCE_API_KEY=your_key
export BINANCE_API_SECRET=your_secret
```

---

## How to Run

### Check connectivity

```bash
python cli.py ping
```

### Place a MARKET order

```bash
# Buy 0.01 BTC at market price
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a LIMIT order

```bash
# Sell 0.01 BTC with a limit price of 100000 USDT
python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 100000
```

### Place a STOP_MARKET order (bonus order type)

```bash
# Stop-market sell triggered at 90000
python cli.py place-order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 90000
```

### Dry-run (preview without submitting)

```bash
python cli.py place-order --symbol ETHUSDT --side BUY --type MARKET --quantity 0.1 --dry-run
```

### Pass credentials via flags (overrides .env)

```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Help

```bash
python cli.py --help
python cli.py place-order --help
```

---

## Logging

Log files are written to `logs/trading_bot_YYYYMMDD.log`.

- **Console**: INFO level and above (clean, human-readable).
- **File**: DEBUG level and above (full request/response detail).

Sample log entries are included in the `logs/` directory:
- `logs/sample_market_order.log` — example MARKET order run
- `logs/sample_limit_order.log` — example LIMIT order run

---

## Assumptions

- Only USDT-M (linear) futures are targeted; the base URL is hardcoded to `https://testnet.binancefuture.com`.
- `timeInForce` defaults to `GTC` for LIMIT orders.
- Quantity and price are passed as strings to preserve precision (Binance requires string-formatted decimals).
- The bot does not manage leverage or margin mode — configure those on the testnet dashboard if needed.
- Python 3.9+ is recommended.

---

## Example Output

```
────────────────────────────────────────────────────────────
  📋  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.01
  Price      : N/A (MARKET)
  Stop Price : N/A
────────────────────────────────────────────────────────────
  ✅  ORDER PLACED SUCCESSFULLY
────────────────────────────────────────────────────────────
  Order ID        : 3426598741
  Client Order ID : abc123xyz
  Symbol          : BTCUSDT
  Side            : BUY
  Type            : MARKET
  Status          : FILLED
  Quantity        : 0.01
  Executed Qty    : 0.01
  Avg Price       : 96842.30
────────────────────────────────────────────────────────────
```
