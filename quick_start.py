#!/usr/bin/env python3
"""
Quick start script - run this first!
"""

import os
import subprocess
import sys

def run_quick_start():
    print("🚀 IBKR Scalper Quick Start")
    print("=" * 40)
    
    # Create necessary directories
    directories = ['data/backtests', 'data/historical', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Install requirements
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return
    
    # Run the main backtest
    print("\n📊 Running initial backtest...")
    try:
        subprocess.check_call([sys.executable, "main.py"])
    except subprocess.CalledProcessError:
        print("❌ Backtest failed - check the error messages above")
        
    print("\n🎉 Setup complete! You can now:")
    print("1. Review the backtest results")
    print("2. Modify config/settings.py for your preferences")
    print("3. Run main.py again to test changes")
    print("4. Connect to IBKR when ready for live trading")

if __name__ == "__main__":
    run_quick_start()