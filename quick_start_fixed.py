#!/usr/bin/env python3
"""
Fixed Quick Start - Uses simpler dependencies
"""

import os
import subprocess
import sys

def run_quick_start_fixed():
    print("🚀 IBKR Scalper Quick Start (Fixed Version)")
    print("=" * 50)
    
    # Create necessary directories
    directories = ['data/backtests', 'data/historical', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Install simplified requirements
    print("\n📦 Installing simplified dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_simple.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Trying individual package installation...")
        install_individual_packages()
    
    # Run the main backtest
    print("\n📊 Running initial backtest...")
    try:
        # Use the simplified main file we'll create next
        subprocess.check_call([sys.executable, "main_simple.py"])
    except subprocess.CalledProcessError:
        print("❌ Backtest failed - let's try manual setup")
        manual_setup()

def install_individual_packages():
    """Install packages one by one to avoid conflicts"""
    packages = [
        "pandas==1.5.3",
        "numpy==1.21.6", 
        "yfinance==0.2.18",
        "matplotlib==3.5.3",
        "scipy==1.9.3",
        "ib_insync==0.9.86"
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"⚠️  Could not install {package}, continuing...")

def manual_setup():
    """Manual setup if automated fails"""
    print("\n🔧 Manual Setup Instructions:")
    print("1. The basic directories have been created")
    print("2. Try running: python main_simple.py")
    print("3. If that fails, we'll create an even simpler version")

if __name__ == "__main__":
    run_quick_start_fixed()