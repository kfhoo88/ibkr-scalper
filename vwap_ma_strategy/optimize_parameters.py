# vwap_ma_strategy/optimize_parameters.py
"""
Parameter Optimization Engine for QQQ/SPY Scalping Strategy
Systematic grid search to find optimal parameters for 60%+ win rate
"""

import pandas as pd
import numpy as np
import yaml
import itertools
import time
from datetime import datetime
import os
import sys
import subprocess
import json

class ParameterOptimizer:
    def __init__(self, config_path="config/vwap_ma_config.yaml"):
        self.config_path = config_path
        self.results = []
        self.best_params = None
        self.highest_win_rate = 0
        
    def load_base_config(self):
        """Load the base configuration file"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def generate_parameter_grid(self):
        """Generate focused parameter combinations around current values"""
        parameter_grid = {
            'ema_length': [13, 21, 34, 55],
            'ema_backcandles': [8, 10, 13, 21],
            'hl_backcandles': [13, 20, 34, 55],
            'atr_multiplier': [0.7, 1.0, 1.3, 1.5],
            'tp_multiplier': [1.0, 1.3, 1.5, 2.0, 2.5]
        }
        
        # Generate all combinations
        keys = parameter_grid.keys()
        values = parameter_grid.values()
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        print(f"🎯 Generated {len(combinations)} parameter combinations")
        return combinations
    
    def create_modified_config(self, base_config, params):
        """Create a modified config with the given parameters"""
        modified_config = base_config.copy()
        
        # Update reversal_strategy parameters
        modified_config['reversal_strategy'].update({
            'ema_length': params['ema_length'],
            'ema_backcandles': params['ema_backcandles'],
            'hl_backcandles': params['hl_backcandles'],
            'atr_multiplier': params['atr_multiplier'],
            'tp_multiplier': params['tp_multiplier']
        })
        
        return modified_config
    
    def run_backtest(self, params, temp_config_path):
        """Run the backtest with given parameters and return results"""
        try:
            # Run the main analysis script as subprocess
            cmd = [
                'python', 'main_reversal_detailed_with_analysis_fixed.py',
                '--config', temp_config_path,
                '--no-plot'  # Skip plotting for faster execution
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                # Parse results from output or result files
                return self.parse_results(params)
            else:
                print(f"❌ Backtest failed for params {params}: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error running backtest: {e}")
            return None
    
    def parse_results(self, params):
        """Parse backtest results from generated files"""
        try:
            # Load the latest trade analysis
            spy_file = 'trade_analysis_SPY_detailed.csv'
            qqq_file = 'trade_analysis_QQQ_detailed.csv'
            
            if os.path.exists(spy_file) and os.path.exists(qqq_file):
                spy_df = pd.read_csv(spy_file)
                qqq_df = pd.read_csv(qqq_file)
                
                # Combine results
                combined_trades = pd.concat([spy_df, qqq_df], ignore_index=True)
                
                # Calculate metrics
                total_trades = len(combined_trades)
                winning_trades = len(combined_trades[combined_trades['pnl'] > 0])
                win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
                
                total_pnl = combined_trades['pnl'].sum()
                avg_pnl = combined_trades['pnl'].mean()
                
                # Calculate profit factor
                gross_profit = combined_trades[combined_trades['pnl'] > 0]['pnl'].sum()
                gross_loss = abs(combined_trades[combined_trades['pnl'] < 0]['pnl'].sum())
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
                
                return {
                    'params': params,
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'avg_pnl': avg_pnl,
                    'profit_factor': profit_factor,
                    'gross_profit': gross_profit,
                    'gross_loss': gross_loss
                }
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error parsing results: {e}")
            return None
    
    def optimize(self, max_combinations=None):
        """Run the optimization process"""
        print("🚀 STARTING PARAMETER OPTIMIZATION")
        print("=" * 60)
        
        # Load base config
        base_config = self.load_base_config()
        print("✅ Loaded base configuration")
        
        # Generate parameter grid
        param_combinations = self.generate_parameter_grid()
        
        if max_combinations:
            param_combinations = param_combinations[:max_combinations]
            print(f"🔬 Testing first {max_combinations} combinations (for quick testing)")
        
        total_combinations = len(param_combinations)
        print(f"🎯 Testing {total_combinations} parameter combinations")
        
        start_time = time.time()
        
        for i, params in enumerate(param_combinations):
            print(f"\n🔍 Testing combination {i+1}/{total_combinations}:")
            print(f"   EMA: {params['ema_length']}, EMA_Back: {params['ema_backcandles']}")
            print(f"   HL_Back: {params['hl_backcandles']}, ATR_Mult: {params['atr_multiplier']}")
            print(f"   TP_Mult: {params['tp_multiplier']}")
            
            # Create temporary config file
            temp_config = self.create_modified_config(base_config, params)
            temp_config_path = f"temp_config_{i}.yaml"
            
            with open(temp_config_path, 'w') as f:
                yaml.dump(temp_config, f)
            
            # Run backtest
            result = self.run_backtest(params, temp_config_path)
            
            # Clean up temp file
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)
            
            if result:
                self.results.append(result)
                
                # Track best parameters
                if result['win_rate'] > self.highest_win_rate:
                    self.highest_win_rate = result['win_rate']
                    self.best_params = params
                    print(f"🎉 NEW BEST! Win Rate: {result['win_rate']:.2f}%")
                
                print(f"   ✅ Trades: {result['total_trades']}, Win Rate: {result['win_rate']:.2f}%")
                print(f"   💰 PnL: ${result['total_pnl']:.2f}, Profit Factor: {result['profit_factor']:.2f}")
            else:
                print(f"   ❌ Failed to get results")
        
        # Calculate optimization time
        optimization_time = time.time() - start_time
        print(f"\n⏱️  Optimization completed in {optimization_time:.2f} seconds")
        
        # Save results
        self.save_results()
        
        return self.best_params
    
    def save_results(self):
        """Save optimization results to file"""
        if not self.results:
            print("❌ No results to save")
            return
        
        # Create results DataFrame
        results_df = pd.DataFrame(self.results)
        
        # Sort by win rate (primary) and profit factor (secondary)
        results_df = results_df.sort_values(['win_rate', 'profit_factor'], ascending=[False, False])
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"optimization_results_{timestamp}.csv"
        results_df.to_csv(filename, index=False)
        
        # Save best parameters
        best_filename = f"best_parameters_{timestamp}.json"
        with open(best_filename, 'w') as f:
            json.dump({
                'best_params': self.best_params,
                'highest_win_rate': self.highest_win_rate,
                'total_tests': len(self.results)
            }, f, indent=2)
        
        print(f"💾 Results saved to {filename}")
        print(f"💾 Best parameters saved to {best_filename}")
        
        # Print top 10 results
        self.print_top_results(results_df)
    
    def print_top_results(self, results_df, top_n=10):
        """Print top N results"""
        print(f"\n🏆 TOP {top_n} PARAMETER COMBINATIONS:")
        print("=" * 80)
        
        top_results = results_df.head(top_n)
        
        for i, (_, result) in enumerate(top_results.iterrows(), 1):
            print(f"{i:2d}. Win Rate: {result['win_rate']:6.2f}% | "
                  f"Profit Factor: {result['profit_factor']:5.2f} | "
                  f"Total PnL: ${result['total_pnl']:8.2f} | "
                  f"Trades: {result['total_trades']:3d}")
            print(f"    EMA: {result['params']['ema_length']:2d}, "
                  f"EMA_Back: {result['params']['ema_backcandles']:2d}, "
                  f"HL_Back: {result['params']['hl_backcandles']:2d}, "
                  f"ATR_Mult: {result['params']['atr_multiplier']:4.1f}, "
                  f"TP_Mult: {result['params']['tp_multiplier']:4.1f}")
            print()

def run_optimization(max_combinations=None):
    """Run the parameter optimization"""
    print("🎯 QQQ/SPY SCALPING PARAMETER OPTIMIZATION")
    print("Target: 60%+ Win Rate")
    print("=" * 60)
    
    optimizer = ParameterOptimizer()
    
    # Run optimization
    best_params = optimizer.optimize(max_combinations=max_combinations)
    
    if best_params:
        print(f"\n🎉 OPTIMIZATION COMPLETED!")
        print(f"🏆 Best Parameters Found:")
        print(f"   EMA Length: {best_params['ema_length']}")
        print(f"   EMA Backcandles: {best_params['ema_backcandles']}")
        print(f"   HL Backcandles: {best_params['hl_backcandles']}")
        print(f"   ATR Multiplier: {best_params['atr_multiplier']}")
        print(f"   TP Multiplier: {best_params['tp_multiplier']}")
        print(f"   Highest Win Rate: {optimizer.highest_win_rate:.2f}%")
    else:
        print("❌ No valid results found")

if __name__ == "__main__":
    # For quick testing, limit to first 10 combinations
    # Remove max_combinations for full optimization
    run_optimization(max_combinations=10)