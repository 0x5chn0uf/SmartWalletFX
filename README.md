# 🧠 SmartWalletFX

A powerful crypto portfolio tracker providing a centralized overview of all your crypto and DeFi positions, with integrated Smart Money Concepts (SMC) analysis tools.

---

## 🌟 Features

### 📊 Portfolio Overview
- **Wallet Tracking:** Monitor EVM wallet balances and transactions
- **DeFi Integration:** Track positions across Aave, Compound, and Radiant (via direct smart contract calls)
- **Performance Analytics:** View detailed PnL, variations, and historical performance
- **Visual Analytics:** TradingView-style charts with custom indicators

### 🎯 Smart Money Zone (SMC)
- **Technical Indicators:** Fair Value Gaps (FVG), Order Blocks (OB), Breaker Blocks (BB)
- **Multi-timeframe Analysis:** Higher timeframe levels visible on lower timeframes
- **Assets:** BTC and ETH (initial support)

### ⚡ Real-time Alerts
- Price alerts, candle close notifications, market structure events, volatility spikes
- Telegram integration

### 🎨 User Interface
- Dark mode with emerald green accents
- Customizable dashboard, responsive design, intuitive navigation

---

## 🛠 Tech Stack

### Backend
- **Python (FastAPI)** — Modular, hexagonal architecture
- **web3.py** — Direct smart contract calls for DeFi protocols (Aave, Compound, Radiant)
- **CoinGecko API** — Live price oracle for USD values
- **Pydantic** — Data validation and serialization
- **SQLite/TinyDB** — Local database
- **Task Master** — AI-powered task and roadmap management
- **Testing:** Pytest, coverage, extensive unit/integration tests, mocking for web3 and price oracles
- **Code Quality:** Black, isort, flake8, mypy, Bandit, Safety, pre-commit hooks
- **CI/CD:** GitHub Actions (lint, test, security, build, deploy)

### Frontend
- **React**
- **TradingView charting library**
- **Dark mode UI components**

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js & npm
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smartwalletfx.git
   cd smartwalletfx
   ```

2. **Set up backend**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .           # Uses pyproject.toml (editable mode)
   ```

3. **Set up frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (Alchemy, CoinGecko, etc.)
   ```

5. **Run the application**
   ```bash
   # Terminal 1 (Backend)
   cd backend
   uvicorn app.main:app

   # Terminal 2 (Frontend)
   cd frontend
   npm start
   ```

---

## 📝 Development Status

### Current Version
- Modular, production-ready FastAPI backend
- DeFi integration: Aave, Compound, Radiant (via smart contracts)
- CoinGecko price oracle integration
- Robust, fully tested codebase (unit, integration, e2e)
- Task Master for project management, reflection, and roadmap
- All code quality, linting, and CI/CD checks enforced

### Roadmap & Future Improvements
- Multi-oracle support, batch contract calls, advanced protocol abstraction
- Historical data, multi-wallet, CEX integration, cloud hosting
- Advanced SMC indicators, user authentication, improved UI/UX
- See Task Master tasks and docs for details

---

## 🤝 Contributing

- Please open issues for feature requests or bug reports.
- All code must pass Black, isort, flake8, and tests before PRs are accepted.
- See `.github/CONTRIBUTING.md` (if available) for guidelines.

---

## 📜 License

This project is private and not open for public use or distribution at this time.

---

## 🔒 Security

- No MetaMask connection required
- Read-only wallet tracking
- Local data storage
- API keys required for external services (never commit secrets)
- Robust error handling and security checks (Bandit, Safety)

---

## 📞 Support

For questions or support, please open an issue in the repository.

---

Built with ❤️ for crypto traders who value technical analysis and portfolio management.
