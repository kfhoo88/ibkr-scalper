# examine_complete_scalper.py

import sys
import os
sys.path.append('strategies')

def examine_complete_scalper():
    """Examine the CompleteScalpingStrategy to see what features it has"""
    print("🔍 EXAMINING COMPLETE SCALPING STRATEGY")
    print("=" * 50)
    
    try:
        from complete_scalper import CompleteScalpingStrategy
        
        # Create instance and check methods
        strategy = CompleteScalpingStrategy()
        
        print("✅ CompleteScalpingStrategy loaded successfully")
        
        # Check what methods it has
        methods = [method for method in dir(strategy) if not method.startswith('_')]
        print(f"\n📋 Available methods: {len(methods)}")
        
        # Group methods by category
        analysis_methods = [m for m in methods if 'analyze' in m.lower() or 'calculate' in m.lower()]
        risk_methods = [m for m in methods if 'risk' in m.lower() or 'hedge' in m.lower() or 'delta' in m.lower()]
        trade_methods = [m for m in methods if 'trade' in m.lower() or 'position' in m.lower() or 'entry' in m.lower() or 'exit' in m.lower()]
        other_methods = [m for m in methods if m not in analysis_methods + risk_methods + trade_methods]
        
        print(f"\n📊 Analysis methods: {analysis_methods}")
        print(f"🛡️  Risk methods: {risk_methods}")
        print(f"💰 Trade methods: {trade_methods}")
        print(f"📦 Other methods: {other_methods}")
        
        # Check for specific advanced features
        advanced_features = {
            'Hedging': any('hedge' in m.lower() for m in methods),
            'Delta Management': any('delta' in m.lower() for m in methods),
            'Options Support': any('option' in m.lower() for m in methods),
            'Portfolio Risk': any('portfolio' in m.lower() for m in methods),
            'Position Rolling': any('roll' in m.lower() for m in methods),
            'Volatility Adjustment': any('volatility' in m.lower() or 'iv' in m.lower() for m in methods)
        }
        
        print(f"\n🎯 ADVANCED FEATURES CHECK:")
        for feature, exists in advanced_features.items():
            status = "✅" if exists else "❌"
            print(f"   {status} {feature}")
            
        return advanced_features
        
    except Exception as e:
        print(f"❌ Error examining complete scalper: {e}")
        return {}

def compare_strategies():
    """Compare all available strategies"""
    print("\n🔍 COMPARING ALL STRATEGIES")
    print("=" * 50)
    
    strategies_to_check = [
        'ScalpingStrategy',
        'DebugScalpingStrategy', 
        'Scalping1MinStrategy',
        'CompleteScalpingStrategy'
    ]
    
    for strategy_name in strategies_to_check:
        try:
            if strategy_name == 'ScalpingStrategy':
                from scalping_strategy import ScalpingStrategy as Strategy
            elif strategy_name == 'DebugScalpingStrategy':
                from debug_scalper import DebugScalpingStrategy as Strategy
            elif strategy_name == 'Scalping1MinStrategy':
                from scalping_1min import Scalping1MinStrategy as Strategy
            elif strategy_name == 'CompleteScalpingStrategy':
                from complete_scalper import CompleteScalpingStrategy as Strategy
                
            strategy = Strategy()
            methods = [method for method in dir(strategy) if not method.startswith('_')]
            
            # Check for advanced features
            has_hedging = any('hedge' in m.lower() for m in methods)
            has_delta = any('delta' in m.lower() for m in methods)
            has_options = any('option' in m.lower() for m in methods)
            
            print(f"\n{strategy_name}:")
            print(f"   Total methods: {len(methods)}")
            print(f"   Hedging: {'✅' if has_hedging else '❌'}")
            print(f"   Delta Management: {'✅' if has_delta else '❌'}")
            print(f"   Options Support: {'✅' if has_options else '❌'}")
            
        except Exception as e:
            print(f"❌ {strategy_name}: {e}")

if __name__ == "__main__":
    advanced_features = examine_complete_scalper()
    compare_strategies()
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATION")
    print("=" * 60)
    
    # Check if any strategy has advanced features
    if any(advanced_features.values()):
        print("✅ Some advanced features exist in CompleteScalpingStrategy")
        print("   Let's enhance it with missing features")
    else:
        print("❌ No advanced features found in any strategy")
        print("   We need to build them from scratch")
    
    print("\n💡 Next steps:")
    print("1. Add hedging capabilities to working strategy")
    print("2. Implement delta management for options")
    print("3. Build position rolling mechanisms")
    print("4. Create comprehensive risk management")