# check_data_size.py
import pandas as pd
import os
import sys

def check_backtester_data_size():
    """Check what data size the proven backtester is using"""
    
    # Read the proven backtester code
    with open("core/backtester_proven.py", "r") as f:
        content = f.read()
    
    print("🔍 ANALYZING PROVEN BACKTESTER DATA SIZE")
    print("=" * 50)
    
    # Look for sample_size parameter
    if "sample_size" in content:
        # Find the sample_size value
        lines = content.split('\n')
        for line in lines:
            if "sample_size" in line and "=" in line:
                print(f"📊 Found in code: {line.strip()}")
    
    # Check what the current test is actually using
    print(f"\n📈 CURRENT TEST PROGRESS:")
    print(f"   Testing TEST: 594/9980 bars")
    print(f"   This means: 9,980 total bars in this test")
    print(f"   Sample size: ~10,000 bars")
    
    # Compare to full dataset
    data_dir = 'data/historical'
    spy_files = [f for f in os.listdir(data_dir) if f.startswith('SPY') and '1min' in f]
    
    if spy_files:
        file_path = os.path.join(data_dir, spy_files[0])
        data = pd.read_csv(file_path)
        full_size = len(data)
        
        print(f"\n📁 FULL DATASET SIZE:")
        print(f"   {spy_files[0]}: {full_size:,} bars")
        print(f"   Current test uses: {9980:,} bars")
        print(f"   Percentage of full data: {(9980/full_size)*100:.1f}%")
        
        # Calculate time coverage
        if 'date' in data.columns:
            start_date = pd.to_datetime(data['date'].iloc[0])
            end_date = pd.to_datetime(data['date'].iloc[-1])
            total_days = (end_date - start_date).days
            
            test_days = int((9980 / full_size) * total_days)
            print(f"   Time coverage: ~{test_days} days out of {total_days} total days")
    
    # Check the specific line in the code
    print(f"\n🔍 CODE ANALYSIS:")
    if "sample_size=50000" in content:
        print("   The code is set to use sample_size=50000")
        print("   But current test shows only 9,980 bars")
        print("   This might be using synthetic test data")
    else:
        print("   Using configured sample size from code")

if __name__ == "__main__":
    check_backtester_data_size()