# inspect_data.py
import pandas as pd
import os

def inspect_all_data_files():
    """Inspect all data files to understand their structure"""
    data_dir = 'data/historical'
    
    print("🔍 INSPECTING ALL DATA FILES")
    print("=" * 50)
    
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    for file in sorted(files):
        file_path = os.path.join(data_dir, file)
        print(f"\n📁 FILE: {file}")
        print("-" * 30)
        
        try:
            # Load first few rows
            data = pd.read_csv(file_path, nrows=5)
            print(f"   Shape: {data.shape}")
            print(f"   Columns: {list(data.columns)}")
            print(f"   First row date: {data.iloc[0]['date'] if 'date' in data.columns else 'N/A'}")
            
            # Check for timestamp column
            if 'timestamp' in data.columns:
                print("   ✅ Has 'timestamp' column")
            else:
                print("   ❌ No 'timestamp' column")
                
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")

if __name__ == "__main__":
    inspect_all_data_files()