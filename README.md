# 🧠 SmartWalletFX

A powerful crypto portfolio tracker providing a centralized overview of all your crypto and DeFi positions, with integrated Smart Money Concepts (SMC) analysis tools.

---

## 🌟 Features

### 📊 Portfolio Overview
- **Wallet Tracking:** Monitor EVM wallet balances and transactions.
- **DeFi Integration:** Track positions across Aave, Compound, and Radiant using both direct smart contract calls.
- **Performance Timeline:** View historical portfolio performance (collateral, borrows, health score) with data collected by scheduled background jobs.
- **Visual Analytics:** TradingView-style charts with custom indicators.

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
- **web3.py** — Direct smart contract calls
- **CoinGecko API** — Live price oracle for USD values
- **Pydantic** — Data validation and serialization
- **SQLite (via SQLAlchemy)** — Default embedded database for local development (PostgreSQL planned).
- **Celery & Redis** — Asynchronous task queue for background jobs (e.g., periodic portfolio snapshots).
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
- Docker & Docker Compose

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/0x5chn0uf/smartwalletfx.git
   cd smartwalletfx
   ```

2. **Configure environment variables**
   ```bash
   cd backend
   cp env.example .env
   # Edit .env with your API keys (Alchemy, CoinGecko, etc.)
   ```

3. **Set up backend**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .           # Uses pyproject.toml (editable mode)

   # SQLite requires no services; simply run migrations if needed (optional)
   alembic upgrade head
   ```

4. **Set up frontend**
   ```bash
   cd frontend
   npm install
   ```

5. **Run the application**

   > **Note:** By default the backend uses SQLite files (`smartwallet_dev.db`, `smartwallet_test.db`) and therefore **no database container is required**. Redis remains optional for background tasks. A Postgres compose file is included for future migration.

   ```bash
   # Terminal 1 (Backend)
   cd backend
   uvicorn app.main:app

   # Terminal 2 (Celery Worker for background tasks)
   cd backend
   source .venv/bin/activate
   celery -A app.celery_app.celery worker -l info

   # Terminal 3 (Frontend)
   cd frontend
   npm start
   ```

---

## 📝 Development Status

### Current Version
- **Modular Backend:** Production-ready FastAPI backend with a hexagonal architecture.
- **DeFi Integration:** Supports Aave, Compound, and Radiant using both smart contract calls.
- **Performance Timeline:** Includes a Celery-based background scheduler to periodically capture and store portfolio snapshots in a PostgreSQL database.
- **Price Oracles:** Live USD values fetched from CoinGecko with caching.
- **Testing:** High test coverage (>95%) across unit, integration, and E2E tests.
- **Project Management:** All tasks, enhancements, and technical debt are tracked via Task Master.
- **Code Quality:** CI/CD pipeline enforces strict code quality, linting, and security checks.

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
