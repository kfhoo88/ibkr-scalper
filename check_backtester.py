# check_backtester.py
import sys
import os

# Add core to path
sys.path.append('core')

try:
    from backtester import *
    print("✅ Successfully imported from core.backtester")
    print("📋 Available classes/functions:")
    
    # List all available attributes
    import inspect
    for name, obj in inspect.getmembers(sys.modules['backtester']):
        if not name.startswith('_'):
            print(f"   - {name}: {type(obj).__name__}")
            
except Exception as e:
    print(f"❌ Import error: {e}")
    
# Also check the file contents
backtester_path = "core/backtester.py"
if os.path.exists(backtester_path):
    print(f"\n📄 Contents of {backtester_path}:")
    print("=" * 50)
    with open(backtester_path, 'r') as f:
        content = f.read()
        # Show first 500 characters to see the structure
        print(content[:500] + "..." if len(content) > 500 else content)
else:
    print(f"❌ File not found: {backtester_path}")