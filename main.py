#!/usr/bin/env python3
"""
Main execution file for IBKR Options Scalper
"""

import logging
import sys
import os

# Add the package to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.data_manager import DataManager
from analysis.backtest_engine import BacktestEngine
from config import settings

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scalper.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main execution function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 IBKR Options Scalping Package")
    print("=" * 50)
    
    # Initialize data manager
    data_manager = DataManager()
    
    # Download historical data for backtesting
    logger.info("Downloading historical data...")
    historical_data = data_manager.download_historical_data(
        settings.SYMBOLS,
        settings.BACKTEST_START_DATE,
        settings.BACKTEST_END_DATE
    )
    
    if not historical_data:
        logger.error("Failed to download historical data")
        return
        
    # Run backtest
    logger.info("Running backtest...")
    backtest_engine = BacktestEngine(settings.INITIAL_CAPITAL)
    
    # Test on SPY data
    spy_data = historical_data['SPY']
    performance, trades = backtest_engine.run_backtest(spy_data)
    
    # Display results
    print("\n📊 BACKTEST RESULTS")
    print("=" * 30)
    for key, value in performance.items():
        if isinstance(value, float):
            print(f"{key:.<20} {value:>10.2f}")
        else:
            print(f"{key:.<20} {value:>10}")
    
    print(f"\n💡 Next steps:")
    print("1. Review the backtest results above")
    print("2. Check logs/scalper.log for detailed trade information")
    print("3. Run parameter optimization to improve performance")
    print("4. Connect to IBKR for live trading when ready")

if __name__ == "__main__":
    main()