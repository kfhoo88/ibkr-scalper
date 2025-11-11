# check_backtester_structure.py
import os
import importlib.util

def analyze_backtester():
    """Analyze what's actually in the backtester module"""
    print("🔍 ANALYZING core/backtester.py...")
    print("=" * 50)
    
    backtester_path = "core/backtester.py"
    
    if not os.path.exists(backtester_path):
        print("❌ core/backtester.py not found!")
        return
    
    # Read the file content
    with open(backtester_path, 'r') as f:
        content = f.read()
    
    print(f"📏 File size: {len(content)} characters")
    print(f"📋 First 300 characters:")
    print("-" * 40)
    print(content[:300])
    print("-" * 40)
    
    # Look for class definitions
    lines = content.split('\n')
    classes = []
    functions = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('class '):
            classes.append(line)
        elif line.startswith('def ') and not line.startswith('def __'):
            functions.append(line)
    
    print(f"\n🏗️  CLASSES FOUND: {len(classes)}")
    for cls in classes:
        print(f"   • {cls}")
    
    print(f"\n🔧 FUNCTIONS FOUND: {len(functions)}")
    for func in functions[:10]:  # Show first 10 functions
        print(f"   • {func}")
    
    # Check if Backtester class exists
    backtester_exists = any('Backtester' in cls for cls in classes)
    if backtester_exists:
        print(f"\n✅ Backtester class IS defined")
    else:
        print(f"\n❌ Backtester class is NOT defined")
        
    return content, classes, functions

if __name__ == "__main__":
    analyze_backtester()