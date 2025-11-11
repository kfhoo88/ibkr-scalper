# main_fixed.py
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

sys.path.append('core')

try:
    from backtester import OptionsBacktester
    print("✅ Successfully imported OptionsBacktester")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class FixedBacktester:
    def __init__(self):
        self.data_dir = 'data/historical'
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
    def prepare_data_for_backtester(self, symbol):
        """
        Load and prepare data specifically for OptionsBacktester
        """
        print(f"📥 PREPARING DATA FOR {symbol}...")
        
        # Find the 1-minute data file
        files = [f for f in os.listdir(self.data_dir) 
                if f.startswith(symbol) and '1min_1year' in f and 'IBKR' in f]
        
        if not files:
            print(f"❌ No data found for {symbol}")
            return None
        
        file_path = os.path.join(self.data_dir, files[0])
        print(f"   Loading: {files[0]}")
        
        try:
            # Load the data
            data = pd.read_csv(file_path)
            
            # Convert date column to datetime
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                # Create timestamp column that OptionsBacktester might expect
                data['timestamp'] = data['date']
            else:
                print(f"❌ No 'date' column found")
                print(f"   Available columns: {list(data.columns)}")
                return None
            
            # Standardize column names - ensure we have OHLCV in lowercase
            column_mapping = {
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume',
                'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low', 'CLOSE': 'close', 'VOLUME': 'volume'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in data.columns:
                    data[new_col] = data[old_col]
            
            # Ensure we have all required columns
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in data.columns]
            
            if missing_cols:
                print(f"❌ Missing columns: {missing_cols}")
                print(f"   Available: {list(data.columns)}")
                return None
            
            # Set timestamp as index and sort
            data.set_index('timestamp', inplace=True)
            data.sort_index(inplace=True)
            
            print(f"   ✅ Prepared {len(data):,} bars")
            print(f"   📊 Columns: {list(data.columns)}")
            print(f"   📅 Period: {data.index.min()} to {data.index.max()}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error preparing data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_safe_backtest(self, symbol, use_subset=True):
        """
        Run backtest with proper error handling
        """
        print(f"\n🎯 RUNNING SAFE BACKTEST: {symbol}")
        print("=" * 50)
        
        # Prepare the data
        data = self.prepare_data_for_backtester(symbol)
        if data is None:
            return None
        
        # Use subset for testing
        if use_subset:
            data = data.iloc[-5000:]  # Last 5000 bars
            print(f"   Using {len(data):,} bars for safe test")
        
        # Initialize backtester
        try:
            backtester = OptionsBacktester("config/scalping_config.yaml")
            print("   ✅ OptionsBacktester initialized")
        except Exception as e:
            print(f"❌ Error initializing backtester: {e}")
            return None
        
        # Run backtest with detailed error handling
        print(f"   🔄 Starting backtest...")
        
        try:
            start_time = datetime.now()
            results = backtester.backtest(data, symbol=symbol)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            print(f"   ✅ Backtest completed in {duration:.1f} seconds")
            
            return results
            
        except Exception as e:
            print(f"❌ Backtest error: {e}")
            print("🔧 Let's try to understand the error better...")
            
            # Try to run with even smaller data to debug
            print("   🐛 Debugging with tiny dataset...")
            try:
                tiny_data = data.iloc[:100]  # Just 100 bars
                debug_results = backtester.backtest(tiny_data, symbol=symbol)
                print("   ✅ Tiny dataset worked!")
                return debug_results
            except Exception as debug_e:
                print(f"   ❌ Even tiny dataset failed: {debug_e}")
                import traceback
                traceback.print_exc()
            
            return None
    
    def analyze_any_results(self, results, symbol):
        """
        Flexible results analysis that handles any result format
        """
        print(f"\n📊 ANALYZING RESULTS: {symbol}")
        print("=" * 40)
        
        if results is None:
            print("   ❌ No results to analyze")
            return
        
        print(f"   📋 Results type: {type(results)}")
        
        if isinstance(results, dict):
            print("   🗂️  Dictionary results:")
            for key, value in list(results.items())[:10]:  # Show first 10 items
                print(f"      {key}: {value}")
                
        elif isinstance(results, pd.DataFrame):
            print(f"   📊 DataFrame shape: {results.shape}")
            print(f"   📝 Columns: {list(results.columns)}")
            if len(results) > 0:
                print("   Sample data:")
                print(results.head(3))
                
        elif isinstance(results, list):
            print(f"   📋 List with {len(results)} items")
            if len(results) > 0:
                print(f"   First item type: {type(results[0])}")
                print(f"   First item: {results[0]}")
                
        else:
            print(f"   📄 Results: {results}")
    
    def run_diagnostic(self):
        """
        Run a comprehensive diagnostic to identify the issue
        """
        print("🔧 RUNNING COMPREHENSIVE DIAGNOSTIC")
        print("=" * 50)
        
        # Test with SPY data
        symbol = 'SPY'
        data = self.prepare_data_for_backtester(symbol)
        
        if data is None:
            print("❌ Could not prepare data for diagnostic")
            return
        
        # Use very small dataset for diagnostic
        test_data = data.iloc[:100]
        print(f"📊 Using {len(test_data)} bars for diagnostic")
        
        # Initialize backtester
        try:
            backtester = OptionsBacktester("config/scalping_config.yaml")
            print("✅ Backtester initialized for diagnostic")
            
            # Try to run backtest
            print("🔄 Running diagnostic backtest...")
            results = backtester.backtest(test_data, symbol=symbol)
            print("✅ Diagnostic backtest successful!")
            self.analyze_any_results(results, symbol)
            
        except Exception as e:
            print(f"❌ Diagnostic failed: {e}")
            print("🔍 Let's examine the backtester code...")
            
            # Try to identify which line is causing the issue
            import traceback
            traceback.print_exc()
    
    def run_all(self):
        """
        Run backtests for all symbols with proper error handling
        """
        print("🚀 SPY/QQQ SCALPING - SAFE BACKTEST")
        print("=" * 50)
        
        symbols = ['SPY', 'QQQ']
        
        # First run diagnostic
        self.run_diagnostic()
        
        print(f"\n🎯 PROCEEDING WITH MAIN BACKTESTS")
        
        for symbol in symbols:
            results = self.run_safe_backtest(symbol, use_subset=True)
            self.analyze_any_results(results, symbol)
        
        print(f"\n🎉 SAFE BACKTESTING COMPLETE!")

def main():
    """
    Main function with comprehensive error handling
    """
    print("🎯 SPY/QQQ OPTIONS SCALPING - DEBUGGING BACKTEST")
    print("Using Safe Data Preparation and Error Handling")
    print("=" * 60)
    
    backtester = FixedBacktester()
    backtester.run_all()
    
    print(f"\n💡 NEXT STEPS:")
    print("1. Review the diagnostic output above")
    print("2. If errors persist, we'll examine the backtester code")
    print("3. We can modify the backtester to handle the data properly")

if __name__ == "__main__":
    main()