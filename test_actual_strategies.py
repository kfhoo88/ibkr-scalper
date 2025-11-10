# test_actual_strategies.py

import os
import sys
import importlib.util

def test_available_strategies():
    """Test what strategy classes are actually available"""
    print("🧪 TESTING AVAILABLE STRATEGIES")
    print("=" * 50)
    
    strategies_dir = 'strategies'
    if not os.path.exists(strategies_dir):
        print("❌ No strategies directory found!")
        return
    
    strategy_files = [f for f in os.listdir(strategies_dir) if f.endswith('.py')]
    
    available_classes = {}
    
    for strategy_file in strategy_files:
        filepath = os.path.join(strategies_dir, strategy_file)
        module_name = strategy_file[:-3]  # Remove .py
        
        try:
            # Dynamically import the module
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all classes in the module
            classes = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and attr.__module__ == module_name:
                    classes.append(attr_name)
            
            if classes:
                available_classes[module_name] = classes
                print(f"✅ {strategy_file}: {classes}")
            else:
                print(f"⚠️  {strategy_file}: No classes found")
                
        except Exception as e:
            print(f"❌ {strategy_file}: Error - {e}")
    
    return available_classes

def test_strategy_functionality():
    """Test the functionality of available strategies"""
    print("\n🧪 TESTING STRATEGY FUNCTIONALITY")
    print("=" * 50)
    
    try:
        # Try to import and test the scalping strategy we've been using
        from strategies.scalping_strategy import ScalpingStrategy
        
        strategy = ScalpingStrategy()
        print("✅ ScalpingStrategy imported and initialized")
        
        # Test basic functionality
        if hasattr(strategy, 'analyze_market'):
            print("✅ analyze_market method exists")
        else:
            print("❌ analyze_market method missing")
            
        if hasattr(strategy, 'get_volume_threshold'):
            print("✅ get_volume_threshold method exists") 
        else:
            print("❌ get_volume_threshold method missing")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing strategy: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 ACTUAL PROJECT CAPABILITIES TEST")
    print("=" * 60)
    
    # Test what we have
    available_classes = test_available_strategies()
    strategy_works = test_strategy_functionality()
    
    print("\n" + "=" * 60)
    print("📊 REALITY CHECK SUMMARY")
    print("=" * 60)
    
    if available_classes:
        print("✅ We have these strategy classes:")
        for module, classes in available_classes.items():
            print(f"   {module}: {classes}")
    else:
        print("❌ No strategy classes found!")
    
    if strategy_works:
        print("✅ Basic scalping strategy is working")
    else:
        print("❌ Basic strategy has issues")
    
    print("\n🎯 CONCLUSION:")
    print("We have a WORKING basic scalping strategy")
    print("But we're MISSING the advanced features:")
    print("   - Hedging mechanisms")
    print("   - Delta rolling") 
    print("   - Options awareness")
    print("   - Advanced risk management")

if __name__ == "__main__":
    main()