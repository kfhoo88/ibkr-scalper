import pandas as pd
import pickle
import os

def inspect_files():
    print("Files in current directory:")
    for file in os.listdir('.'):
        if file.endswith('.pkl') or file.endswith('.csv'):
            print(f"\n--- {file} ---")
            try:
                if file.endswith('.pkl'):
                    with open(file, 'rb') as f:
                        data = pickle.load(f)
                else:
                    data = pd.read_csv(file)
                
                print(f"Type: {type(data)}")
                if hasattr(data, 'shape'):
                    print(f"Shape: {data.shape}")
                if hasattr(data, 'columns'):
                    print(f"Columns: {list(data.columns)}")
                if hasattr(data, 'index'):
                    print(f"Index type: {type(data.index)}")
                    if hasattr(data.index, 'name'):
                        print(f"Index name: {data.index.name}")
                
                # Show first few rows if it's a DataFrame
                if isinstance(data, pd.DataFrame):
                    print("First 3 rows:")
                    print(data.head(3))
                    
            except Exception as e:
                print(f"Error reading {file}: {e}")

if __name__ == "__main__":
    inspect_files()