# fix_backtester.py
import os

def examine_backtester_code():
    """Examine the backtester code to find and fix the timestamp issue"""
    backtester_path = "core/backtester.py"
    
    print("🔍 EXAMINING BACKTESTER CODE FOR TIMESTAMP ISSUE")
    print("=" * 50)
    
    with open(backtester_path, 'r') as f:
        lines = f.readlines()
    
    # Find line 224 and surrounding context
    print("📄 Lines around the error (220-230):")
    print("-" * 40)
    for i in range(219, min(230, len(lines))):
        print(f"{i+1:3d}: {lines[i]}", end='')
    print("-" * 40)
    
    # Look for all timestamp references
    print("\n🔍 SEARCHING FOR ALL 'timestamp' REFERENCES:")
    timestamp_lines = []
    for i, line in enumerate(lines):
        if 'timestamp' in line:
            timestamp_lines.append((i+1, line.strip()))
    
    for line_num, line_content in timestamp_lines:
        print(f"Line {line_num}: {line_content}")
    
    return lines

def create_fixed_backtester():
    """Create a fixed version of the backtester that uses 'date' instead of 'timestamp'"""
    print("\n🔧 CREATING FIXED BACKTESTER...")
    
    # Read the original file
    with open("core/backtester.py", 'r') as f:
        content = f.read()
    
    # Replace timestamp with date in the problematic line
    fixed_content = content.replace(
        "print(f\"📊 Data: {len(data)} bars | Period: {data['timestamp'].iloc[0]} to {data['timestamp'].iloc[-1]}\")",
        "print(f\"📊 Data: {len(data)} bars | Period: {data.index[0]} to {data.index[-1]}\")"
    )
    
    # Also replace any other timestamp column references with index
    fixed_content = fixed_content.replace("data['timestamp']", "data.index")
    fixed_content = fixed_content.replace("row['timestamp']", "row.name")
    
    # Write the fixed version
    with open("core/backtester_fixed.py", 'w') as f:
        f.write(fixed_content)
    
    print("✅ Created core/backtester_fixed.py")
    
    # Also create a simple patch that just fixes the specific line
    patch_content = '''# backtester_patch.py
import sys
sys.path.append('core')

# Monkey patch the backtester to fix the timestamp issue
from backtester import OptionsBacktester

original_backtest = OptionsBacktester.backtest

def fixed_backtest(self, data, symbol='SPY'):
    """Fixed backtest method that uses index instead of timestamp column"""
    # Ensure data has proper index
    if 'date' in data.columns and not isinstance(data.index, pd.DatetimeIndex):
        data = data.set_index('date')
    
    # Use index for timestamp display
    print(f"📊 Data: {len(data)} bars | Period: {data.index[0]} to {data.index[-1]}")
    
    # Call original method but with fixed data
    return original_backtest(self, data, symbol)

# Apply the patch
OptionsBacktester.backtest = fixed_backtest

print("✅ Applied timestamp fix patch")
'''
    
    with open("backtester_patch.py", 'w') as f:
        f.write(patch_content)
    
    print("✅ Created backtester_patch.py")

if __name__ == "__main__":
    lines = examine_backtester_code()
    create_fixed_backtester()