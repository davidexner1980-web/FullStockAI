# FullStock AI vNext Ultimate

## Overview

FullStock AI vNext Ultimate is an advanced Flask-based stock prediction platform that combines multiple machine learning models (Random Forest, LSTM, XGBoost), deep learning networks, sentiment analysis, and mystical Oracle insights for comprehensive market analysis. The platform has evolved into a sophisticated AI intelligence system with autonomous capabilities, featuring strategic evolution modules including Neuro-Symbolic Fusion (Oracle Dreams), Curiosity Engine for anomaly detection, and comprehensive backtesting capabilities. It supports both traditional stock and cryptocurrency predictions with real-time data integration from Yahoo Finance.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### MASTER BUILD Folder Structure (Updated 2025-08-07)
```
/project-root/
├── server/                    (Main server directory)
│   ├── api/                   (Flask routes and endpoints)
│   ├── models/                (Trained ML model binaries)
│   ├── ml/                    (ML pipeline and data fetching)
│   ├── tasks/                 (Background tasks - APScheduler)
│   ├── utils/                 (Services and strategic modules)
│   ├── static/                (CSS, JS, PWA assets)
│   ├── templates/             (Jinja2 HTML templates)
│   ├── app.py                 (Main Flask application)
│   ├── config.py              (Environment configuration)
│   └── scheduler.py           (Background task scheduler)
├── frontend/                  (Standalone frontend assets)
│   ├── js/                    (Advanced JavaScript modules)
│   ├── css/                   (Responsive Bootstrap styling)
│   └── index.html             (Complete UI implementation)
├── docs/                      (System documentation and reports)
├── database/                  (Data storage and logs)
├── .replit                    (Replit configuration)
└── main.py                    (Application entry point)
```

### Frontend Architecture
- **Framework**: Flask-based web application with Bootstrap 5 dark theme
- **UI Design**: Modern responsive card-based layout with mobile-first approach
- **Real-time Features**: Socket.IO integration for live price updates and notifications
- **Progressive Web App**: Service worker implementation for offline functionality and caching
- **Visualization**: Chart.js integration for dynamic charts and prediction overlays
- **Mobile Support**: Dedicated mobile CSS and gesture handling

### Backend Architecture
- **Web Framework**: Flask with SQLAlchemy ORM using DeclarativeBase
- **Database**: PostgreSQL with SQLite fallback configuration (via DATABASE_URL)
- **Caching**: Flask-Caching with SimpleCache for performance optimization
- **Background Tasks**: APScheduler for periodic model updates and market data refresh
- **WebSocket Support**: Flask-SocketIO for real-time communication
- **API Design**: RESTful endpoints with comprehensive error handling and caching

### Machine Learning Pipeline
- **Multi-Model Approach**: Random Forest, LSTM, and XGBoost ensemble predictions
- **Feature Engineering**: Technical indicators (RSI, MACD, Bollinger Bands, moving averages)
- **Model Management**: Automatic model training, caching, and periodic retraining
- **Crypto Support**: Specialized cryptocurrency prediction engine with crypto-specific indicators
- **Backtesting Engine**: Comprehensive strategy validation with multiple trading algorithms

### Data Architecture
- **Primary Data Source**: Yahoo Finance via yfinance library
- **Data Fetching**: Cached data fetcher with session management and retry logic
- **Real-time Updates**: Background tasks for periodic market data synchronization
- **Technical Analysis**: TA-Lib integration for advanced technical indicators
- **Sentiment Analysis**: TextBlob and VADER sentiment analysis for market psychology

### Strategic Intelligence Modules
- **Oracle Dreams**: Neuro-symbolic fusion for market consciousness insights
- **Curiosity Engine**: Anomaly detection using Isolation Forest and statistical methods
- **Health Monitor**: System performance and model accuracy tracking
- **Explainability Service**: AI transparency with feature importance analysis
- **Portfolio Analyzer**: Risk assessment and optimization recommendations
- **Quantum Forecast**: Advanced multi-timeframe prediction synthesis

### Authentication & Security
- **Session Management**: Flask session handling with configurable secret keys
- **Environment-based Config**: Secure credential management through environment variables
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxies
- **Input Validation**: Comprehensive input sanitization and error handling

## External Dependencies

### Core Data Providers
- **Yahoo Finance**: Primary data source via yfinance library for stocks and cryptocurrencies
- **Alternative Data APIs**: Fear & Greed Index for cryptocurrency sentiment analysis

### Machine Learning & Analytics
- **scikit-learn**: Random Forest, preprocessing, and anomaly detection algorithms
- **XGBoost**: Gradient boosting for advanced predictions
- **TensorFlow/Keras**: LSTM neural networks for time series forecasting
- **TA-Lib**: Technical analysis library for advanced indicators
- **pandas/numpy**: Data manipulation and numerical computation

### Communication & Notifications
- **Flask-Mail**: Email notification system for price alerts
- **SMTP Integration**: Gmail SMTP for email delivery (configurable)
- **Socket.IO**: Real-time WebSocket communication for live updates

### Frontend Libraries (CDN)
- **Bootstrap 5**: UI framework from Replit CDN
- **Chart.js**: Interactive charting library for data visualization
- **Feather Icons**: Icon system for modern UI elements
- **Font Awesome**: Additional icon library for enhanced UI

### Background Processing
- **APScheduler**: Task scheduling for model updates and data synchronization
- **Threading**: Concurrent processing for real-time monitoring
- **Joblib**: Model serialization and caching

### Development & Deployment
- **Werkzeug**: WSGI utilities and development server
- **Gunicorn**: Production WSGI server support
- **Environment Variables**: Configuration management for API keys and database URLs