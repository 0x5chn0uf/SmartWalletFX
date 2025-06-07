# 🧠 SmartWalletFX

A powerful crypto portfolio tracker that provides a centralized overview of all your crypto positions across different platforms, with integrated Smart Money Concepts (SMC) analysis tools.

## 🌟 Features

### 📊 Portfolio Overview
- **Wallet Tracking**: Monitor EVM wallet balances and transactions
- **DeFi Integration**: Track positions across Aave, Compound, and Radiant protocols
- **Performance Analytics**: View detailed PnL, variations, and historical performance
- **Visual Analytics**: TradingView-style charts with custom indicators

### 🎯 Smart Money Zone (SMC)
- **Technical Indicators**: 
  - Fair Value Gaps (FVG)
  - Order Blocks (OB)
  - Breaker Blocks (BB)
- **Multi-timeframe Analysis**: Higher timeframe levels visible on lower timeframes
- **Assets**: BTC and ETH (initial support)

### ⚡ Real-time Alerts
- Price alerts
- Candle close notifications
- Market structure events
- Volatility spikes
- Telegram integration

### 🎨 User Interface
- Dark mode with emerald green accents
- Customizable dashboard
- Responsive design
- Intuitive navigation

## 🛠 Tech Stack

### Backend
- Python (FastAPI/Flask)
- Local database (TinyDB/SQLite)
- API integrations:
  - Alchemy
  - Etherscan
  - CoinGecko
  - DeBank

### Frontend
- React
- TradingView charting library
- Dark mode UI components

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- Node.js & npm
- Git

### Installation
1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/smartwalletfx.git
   cd smartwalletfx
   ```

2. Set up backend
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up frontend
   ```bash
   cd frontend
   npm install
   ```

4. Configure environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. Run the application
   ```bash
   # Terminal 1 (Backend)
   cd backend
   python main.py

   # Terminal 2 (Frontend)
   cd frontend
   npm start
   ```

## 📝 Development Status

### Current Version (V1)
- Personal use focus
- Single EVM wallet support
- Manual wallet input
- Basic SMC indicators
- Local hosting only

### Upcoming Features (V2+)
- Multi-wallet support
- Advanced SMC indicators
- CEX integration
- Cloud hosting option
- User authentication

## 🤝 Contributing

This project is currently in development. Feel free to open issues for feature requests or bug reports.

## 📜 License

This project is private and not open for public use or distribution at this time.

## 🔒 Security

- No MetaMask connection required
- Read-only wallet tracking
- Local data storage
- API keys required for external services

## 📞 Support

For questions or support, please open an issue in the repository.

---
Built with ❤️ for crypto traders who value technical analysis and portfolio management 