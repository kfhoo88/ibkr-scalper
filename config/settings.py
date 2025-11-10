"""
Configuration settings for IBKR Options Scalping Package
"""

# Trading Parameters
SYMBOLS = ['SPY', 'QQQ']
MAX_POSITION_SIZE = 10000
MAX_LOSS_PER_TRADE = 200
DELTA_THRESHOLD = 0.3

# Volatility Parameters
VIX_LOWER_BOUND = 16
VIX_UPPER_BOUND = 35
MIN_HISTORICAL_VOL = 0.15
VOLUME_MULTIPLIER = 1.2

# Strategy Parameters
SCALPING_TIME_FRAME = '1 min'
PROFIT_TARGET = 0.10
STOP_LOSS = 0.20
MIN_TREND_STRENGTH = 0.6

# Backtesting Parameters
BACKTEST_START_DATE = '2023-01-01'
BACKTEST_END_DATE = '2024-01-01'
INITIAL_CAPITAL = 100000

# Risk Management
MAX_POSITIONS = 3
DAILY_LOSS_LIMIT = 500
BASE_POSITION_SIZE = 1

# IBKR Connection
IBKR_HOST = '127.0.0.1'
IBKR_PORT = 7497  # TWS: 7497, Gateway: 4001
CLIENT_ID = 1
PAPER_TRADING = True

# Optimization Parameters
OPTIMIZATION_METRIC = 'sharpe_ratio'
PARAMETER_RANGES = {
    'ha_lookback': [2, 3, 4],
    'min_trend_strength': [0.5, 0.6, 0.7],
    'profit_target': [0.08, 0.10, 0.12],
    'stop_loss': [0.15, 0.20, 0.25]
}