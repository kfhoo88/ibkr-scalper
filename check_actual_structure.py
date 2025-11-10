# check_actual_structure.py

import os
import sys

def analyze_current_project():
    """Analyze what we actually have in the project"""
    print("🔍 ANALYZING CURRENT PROJECT STRUCTURE")
    print("=" * 60)
    
    # Check main directory
    print("📁 Main directory contents:")
    for item in os.listdir('.'):
        if os.path.isdir(item):
            print(f"   📂 {item}/")
        elif item.endswith('.py'):
            print(f"   📄 {item}")
    
    # Check strategies directory
    strategies_dir = 'strategies'
    if os.path.exists(strategies_dir):
        print(f"\n📁 {strategies_dir}/ contents:")
        for item in os.listdir(strategies_dir):
            if item.endswith('.py'):
                print(f"   📄 {item}")
                # Show file size to understand complexity
                filepath = os.path.join(strategies_dir, item)
                size = os.path.getsize(filepath)
                print(f"      Size: {size} bytes")
    else:
        print(f"\n❌ {strategies_dir}/ directory not found!")
    
    # Check for data directories
    data_dirs = ['data', 'data/historical']
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            print(f"\n📁 {data_dir}/ contents:")
            for item in os.listdir(data_dir):
                if item.endswith('.csv'):
                    print(f"   📊 {item}")
                    filepath = os.path.join(data_dir, item)
                    size = os.path.getsize(filepath)
                    print(f"      Size: {size} bytes")
    
    # Check for any risk or execution directories
    other_dirs = ['risk', 'execution', 'analysis', 'backtesting']
    for other_dir in other_dirs:
        if os.path.exists(other_dir):
            print(f"\n📁 {other_dir}/ exists!")
            for item in os.listdir(other_dir):
                print(f"   📄 {item}")

if __name__ == "__main__":
    analyze_current_project()