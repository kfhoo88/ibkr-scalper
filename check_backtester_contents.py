# check_backtester_contents.py
import os

def check_backtester_file():
    """Check the actual contents of backtester.py"""
    backtester_path = "core/backtester.py"
    
    if not os.path.exists(backtester_path):
        print("❌ core/backtester.py does not exist!")
        return
    
    print("🔍 CHECKING core/backtester.py CONTENTS:")
    print("=" * 50)
    
    with open(backtester_path, 'r') as f:
        content = f.read()
    
    print(f"File size: {len(content)} characters")
    print(f"First 500 characters:")
    print("-" * 30)
    print(content[:500])
    print("-" * 30)
    
    # Check if Backtester class is defined
    if 'class Backtester' in content:
        print("✅ Backtester class IS defined in the file")
    else:
        print("❌ Backtester class is NOT defined in the file")
    
    # Check what classes/functions are defined
    lines = content.split('\n')
    classes = [line for line in lines if line.strip().startswith('class ')]
    functions = [line for line in lines if line.strip().startswith('def ') and not line.strip().startswith('def __')]
    
    if classes:
        print(f"📋 Classes found: {len(classes)}")
        for cls in classes:
            print(f"   • {cls.strip()}")
    else:
        print("📋 No classes found")
    
    if functions:
        print(f"📋 Functions found: {len(functions)}")
        for func in functions[:5]:  # Show first 5
            print(f"   • {func.strip()}")
    else:
        print("📋 No functions found")

if __name__ == "__main__":
    check_backtester_file()
