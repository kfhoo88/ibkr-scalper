# run_fixed_balanced.py - FIXED BACKTESTER IMPORT
import pandas as pd
import sys
import os
import traceback

sys.path.append('strategies')

print("🔍 DEBUG: Starting script...")

try:
    from balanced_advanced_scalper_fixed import BalancedAdvancedScalpingStrategyFixed
    print("✅ DEBUG: Strategy imported successfully")
except ImportError as e:
    print(f"❌ DEBUG: Import failed: {e}")
    sys.exit(1)

def main():
    print("🚀 RUNNING FIXED BALANCED ADVANCED STRATEGY")
    print("============================================================")
    
    # Load data
    data_path = "data/historical/SPY_1min_data.csv"
    print(f"🔍 DEBUG: Loading data from {data_path}")
    
    try:
        data = pd.read_csv(data_path)
        print(f"✅ DEBUG: Data loaded, shape: {data.shape}")
        
        # Fix timestamp column
        if 'Unnamed: 0' in data.columns:
            print("🔍 DEBUG: Using 'Unnamed: 0' as timestamp column")
            data = data.rename(columns={'Unnamed: 0': 'timestamp'})
            data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        print(f"📊 Data loaded: {len(data)} bars")
        print(f"🔍 DEBUG: First timestamp: {data['timestamp'].iloc[0]}")
        print(f"🔍 DEBUG: Last timestamp: {data['timestamp'].iloc[-1]}")
        
    except Exception as e:
        print(f"❌ DEBUG: Data loading failed: {e}")
        traceback.print_exc()
        return
    
    # Initialize strategy
    print("🔍 DEBUG: Initializing strategy...")
    try:
        strategy = BalancedAdvancedScalpingStrategyFixed()
        print("✅ DEBUG: Strategy initialized with default parameters")
    except Exception as e:
        print(f"❌ DEBUG: Strategy initialization failed: {e}")
        traceback.print_exc()
        return
    
    # Initialize backtester - FIXED: Discover correct class name
    print("🔍 DEBUG: Importing backtester...")
    try:
        # First, let's see what classes are available in the backtester
        import advanced_backtester_controlled as backtester_module
        
        # List all classes in the module
        backtester_classes = [cls for cls in dir(backtester_module) 
                            if not cls.startswith('_') and 
                            'backtest' in cls.lower()]
        
        print(f"🔍 DEBUG: Available backtester classes: {backtester_classes}")
        
        if not backtester_classes:
            print("❌ DEBUG: No backtester classes found. Available items:")
            for item in dir(backtester_module):
                if not item.startswith('_'):
                    print(f"   - {item}")
            return
        
        # Use the first backtester class we find
        backtester_class = getattr(backtester_module, backtester_classes[0])
        print(f"✅ DEBUG: Using backtester class: {backtester_classes[0]}")
        
        backtester = backtester_class(strategy)
        print("✅ DEBUG: Backtester initialized")
        
    except Exception as e:
        print(f"❌ DEBUG: Backtester initialization failed: {e}")
        print("🔍 DEBUG: Let's check the backtester file structure...")
        
        # Check what's in the backtester file
        try:
            with open('advanced_backtester_controlled.py', 'r') as f:
                content = f.read()
                # Find class definitions
                import re
                classes = re.findall(r'class\s+(\w+)', content)
                print("Classes in advanced_backtester_controlled.py:")
                for cls in classes:
                    print(f"   - {cls}")
        except Exception as file_error:
            print(f"❌ DEBUG: Could not read backtester file: {file_error}")
        
        return
    
    print("🚀 CONTROLLED ADVANCED BACKTEST: SPY")
    print("============================================================")
    
    # Run backtest
    print("🔍 DEBUG: Starting backtest...")
    try:
        report = backtester.backtest(data, 'SPY')
        print("\n✅ BACKTEST COMPLETED SUCCESSFULLY!")
        if report:
            print(report)
        else:
            print("⚠️  Report is empty")
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
    print("🔍 DEBUG: Script finished")