# check_package_structure.py

import os

def check_package_structure():
    """Check if all expected package files exist"""
    print("📁 CHECKING PACKAGE STRUCTURE")
    print("=" * 50)
    
    expected_dirs = [
        'strategies/',
        'risk/', 
        'execution/',
        'analysis/',
        'data/options/',
        'data/historical/'
    ]
    
    expected_files = [
        # Core strategies
        'strategies/comprehensive_scalper.py',
        'strategies/options_scalper.py', 
        'strategies/volatility_strategy.py',
        
        # Risk management
        'risk/hedge_manager.py',
        'risk/position_manager.py',
        'risk/portfolio_optimizer.py',
        
        # Advanced backtesting
        'backtesting/options_backtester.py',
        'backtesting/advanced_metrics.py',
        
        # Data management
        'data/options_data_manager.py'
    ]
    
    print("Checking directories:")
    for directory in expected_dirs:
        if os.path.exists(directory):
            print(f"✅ {directory}")
        else:
            print(f"❌ {directory} - MISSING")
    
    print("\nChecking key files:")
    for filepath in expected_files:
        if os.path.exists(filepath):
            print(f"✅ {filepath}")
        else:
            print(f"❌ {filepath} - MISSING")
    
    # Check for any Python files in strategies directory
    print("\n📊 Existing strategy files:")
    strategies_dir = 'strategies/'
    if os.path.exists(strategies_dir):
        for file in os.listdir(strategies_dir):
            if file.endswith('.py'):
                print(f"   📄 {file}")

if __name__ == "__main__":
    check_package_structure()