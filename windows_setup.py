# windows_setup.py
import sys
import os
import platform

def check_environment():
    """Check the Windows environment and dependencies"""
    print("🖥️  WINDOWS 10 SETUP CHECK")
    print("=" * 50)
    
    # System info
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Check core dependencies
    dependencies = ['pandas', 'numpy', 'yaml', 'matplotlib', 'seaborn']
    
    print(f"\n📦 CHECKING DEPENDENCIES:")
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} - installing...")
            os.system(f"pip install {dep}")
    
    # Check project structure
    print(f"\n📁 CHECKING PROJECT STRUCTURE:")
    required_dirs = ['core', 'config', 'data/historical']
    required_files = ['main_full_year.py', 'core/backtester_enhanced.py']
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ❌ {dir_path}/ - creating...")
            os.makedirs(dir_path, exist_ok=True)
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
    
    # Check data files
    print(f"\n📊 CHECKING DATA FILES:")
    data_dir = 'data/historical'
    if os.path.exists(data_dir):
        data_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        spy_files = [f for f in data_files if 'SPY' in f and '1min' in f]
        qqq_files = [f for f in data_files if 'QQQ' in f and '1min' in f]
        
        print(f"   Total data files: {len(data_files)}")
        print(f"   SPY 1-min files: {len(spy_files)}")
        print(f"   QQQ 1-min files: {len(qqq_files)}")
        
        if spy_files:
            print(f"   ✅ SPY data: {spy_files[0]}")
        if qqq_files:
            print(f"   ✅ QQQ data: {qqq_files[0]}")
    else:
        print(f"   ❌ No data directory found")
    
    print(f"\n🎉 SETUP COMPLETE!")
    return True

if __name__ == "__main__":
    check_environment()