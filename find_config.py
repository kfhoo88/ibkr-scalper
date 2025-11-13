# Let me examine the current config structure
import yaml
import os

config_path = "vwap_ma_strategy/config/vwap_ma_config.yaml"
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("Current config structure:")
    print(yaml.dump(config, default_flow_style=False))
    
    # Check for time-related parameters
    if 'trading_hours' in config:
        print("\n📅 TRADING HOURS CONFIGURED:")
        print(f"  {config['trading_hours']}")
    
    if 'max_hold_period' in config:
        print(f"\n⏰ MAX HOLD PERIOD: {config['max_hold_period']}")
    
    if 'avoid_periods' in config:
        print(f"\n🚫 AVOID PERIODS: {config['avoid_periods']}")
    
    # Check reversal strategy specific config
    if 'reversal_strategy' in config:
        print(f"\n🎯 REVERSAL STRATEGY CONFIG:")
        reversal_config = config['reversal_strategy']
        for key, value in reversal_config.items():
            print(f"  {key}: {value}")
else:
    print(f"Config file not found at: {config_path}")

# Let me also check if there are any time filters in the main strategy code
print(f"\n🔍 Checking for time filters in strategy code...")

# Common time filter patterns to look for
time_patterns = [
    'market_hours', 'trading_hours', 'max_hold', 'avoid', 
    'lunch', 'open_time', 'close_time', '9:30', '16:00',
    'market_open', 'market_close'
]

strategy_files = []
for root, dirs, files in os.walk('vwap_ma_strategy'):
    for file in files:
        if file.endswith('.py') and 'reversal' in file.lower():
            strategy_files.append(os.path.join(root, file))

for strategy_file in strategy_files[:2]:  # Check first 2 strategy files
    print(f"\n📄 Checking: {strategy_file}")
    try:
        with open(strategy_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            
            time_related_lines = []
            for i, line in enumerate(lines):
                if any(pattern in line.lower() for pattern in time_patterns):
                    time_related_lines.append(f"  Line {i+1}: {line.strip()}")
            
            if time_related_lines:
                print("Time-related code found:")
                for line in time_related_lines[:5]:  # Show first 5 matches
                    print(line)
            else:
                print("  No time filters found in this file")
    except Exception as e:
        print(f"  Error reading file: {e}")