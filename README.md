# 🚀 WalletAnalysis DarpServer

A comprehensive cryptocurrency analysis platform that combines blockchain data analysis, wallet behavior tracking to provide deep insights into crypto markets and trading activities.

## ✨ Features


### 💰 Wallet Analytics
- 📊 Calculate total trading profit 
- 🔍 Track purchased tokens history
- 💎 Per-token profit analysis
- 📈 Portfolio performance tracking
- 🎯 Trading win rate calculation
- 🤖 Trading Bot detection
- 💰 Token price retrieval


## 🛠️ Environment Setup

### API Configuration
Create a `.env` file with required configuration:
```env
SOLANA_RPC=          # Your Solana RPC endpoint (default: https://api.mainnet-beta.solana.com)
```

## 🚀 Quick Start

We use UV as our Python package installer and runner. UV is much faster than pip and provides better dependency resolution.

### Prerequisites
- Python 3.10
- UV package manager

### Install UV

**Unix-like systems (Linux/macOS):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Using pip:**
```bash
pip install uv
```

### Start Server

Run the server using UV:
```bash
uv run ./src/server.py
```

The server will start on `0.0.0.0:3005` by default.

## 📊 Functions

### Wallet Analysis 
- `calculate-total-profit` - Calculate 7-day total profit
- `get-purchased-tokens` - List tokens purchased in last 7 days
- `calculate-profit-per-token` - Calculate profit for specific token
- `calculate-profit-for-each-token` - Calculate profit for all tokens
- `calculate-win-rate` - Calculate trading win rate
- `is-bot-trading` - Detect bot trading behavior
- `get-token-price` - Get a token's price by its mint address

## 📝 Logging

All operations are automatically logged in the `logs` directory for monitoring and debugging purposes, including:
- Transaction analysis results
- API requests and responses
- Error tracking
- Performance metrics

## 🔨 Development

### Built With
- Python 3.10
- Solana Web3 Libraries

### Key Components
- Transaction Analysis Engine
- Market Data Aggregator
- Bot Detection Algorithm

---
