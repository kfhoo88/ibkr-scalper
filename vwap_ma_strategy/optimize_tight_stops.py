# vwap_ma_strategy/optimize_tight_stops.py
"""
Focused Optimization with Tight Stops & Better Risk/Reward
Tests swing_low - tick stops with improved TP multipliers
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

class TightStopsOptimizer:
    def __init__(self, config_path="config/vwap_ma_config.yaml"):
        self.config_path = config_path
        self.results = []
        self.best_win_rate = 0
        self.best_profit_factor = 0
        self.best_params = None
        
    def generate_parameter_grid(self):
        """Generate focused parameter combinations with tight stops"""
        parameter_grid = {
            'ema_length': [20, 30],           # Best performers from previous optimization
            'ema_backcandles': [7, 21],       # Best performers
            'hl_backcandles': [7, 14],        # Best performers
            'sl_tick_distance': [0.02],       # Fixed: swing_low - 0.02 / swing_high + 0.02
            'tp_multiplier': [1.5, 2.0, 2.5, 3.0]  # Test better R/R ratios
        }
        
        # Generate all combinations
        keys = parameter_grid.keys()
        values = parameter_grid.values()
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        total_combinations = len(combinations)
        print(f"🎯 TIGHT STOPS OPTIMIZATION GRID:")
        print(f"   EMA Length: {parameter_grid['ema_length']}")
        print(f"   EMA Backcandles: {parameter_grid['ema_backcandles']}")
        print(f"   HL Backcandles: {parameter_grid['hl_backcandles']}")
        print(f"   SL Tick Distance: {parameter_grid['sl_tick_distance']}")
        print(f"   TP Multipliers: {parameter_grid['tp_multiplier']}")
        print(f"   TOTAL COMBINATIONS: {total_combinations}")
        
        return combinations
    
    def create_modified_config(self, base_config, params):
        """Create modified config with tight stop parameters"""
        modified_config = base_config.copy()
        
        # Update reversal strategy parameters
        modified_config['reversal_strategy'].update({
            'ema_length': params['ema_length'],
            'ema_backcandles': params['ema_backcandles'],
            'hl_backcandles': params['hl_backcandles'],
            'sl_tick_distance': params['sl_tick_distance'],  # New parameter
            'tp_multiplier': params['tp_multiplier']
        })
        
        return modified_config
    
    def run_backtest(self, params, temp_config_path):
        """Run backtest with tight stop parameters"""
        try:
            cmd = [
                'python', 'main_reversal_detailed_with_analysis_fixed.py',
                '--config', temp_config_path,
                '--no-plot'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='.', timeout=120)
            
            if result.returncode == 0:
                return self.parse_results(params)
            else:
                print(f"    ❌ Backtest failed: {result.stderr[:200]}...")
                return None
                
        except subprocess.TimeoutExpired:
            print("    ⏰ Backtest timed out")
            return None
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return None
    
    def parse_results(self, params):
        """Parse backtest results from generated files"""
        try:
            # Load trade analysis files
            spy_file = 'trade_analysis_SPY_detailed.csv'
            qqq_file = 'trade_analysis_QQQ_detailed.csv'
            
            if os.path.exists(spy_file) and os.path.exists(qqq_file):
                spy_df = pd.read_csv(spy_file)
                qqq_df = pd.read_csv(qqq_file)
                
                # Combine results
                combined_trades = pd.concat([spy_df, qqq_df], ignore_index=True)
                
                if len(combined_trades) == 0:
                    return None
                
                # Calculate metrics
                total_trades = len(combined_trades)
                winning_trades = len(combined_trades[combined_trades['pnl'] > 0])
                win_rate = (winning_trades / total_trades) * 100
                
                total_pnl = combined_trades['pnl'].sum()
                avg_pnl = combined_trades['pnl'].mean()
                
                # Calculate profit factor
                gross_profit = combined_trades[combined_trades['pnl'] > 0]['pnl'].sum()
                gross_loss = abs(combined_trades[combined_trades['pnl'] < 0]['pnl'].sum())
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
                
                # Calculate risk/reward statistics
                avg_win = combined_trades[combined_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
                avg_loss = combined_trades[combined_trades['pnl'] < 0]['pnl'].mean() if (total_trades - winning_trades) > 0 else 0
                avg_rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
                
                return {
                    'params': params,
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'avg_pnl': avg_pnl,
                    'profit_factor': profit_factor,
                    'gross_profit': gross_profit,
                    'gross_loss': gross_loss,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'avg_rr_ratio': avg_rr_ratio,
                    'winning_trades': winning_trades,
                    'losing_trades': total_trades - winning_trades
                }
            return None
            
        except Exception as e:
            print(f"    ❌ Error parsing results: {e}")
            return None
    
    def optimize(self):
        """Run the tight stops optimization"""
        print("🚀 TIGHT STOPS OPTIMIZATION")
        print("=" * 70)
        print("Testing: Swing_Low - 0.02 stops with improved R/R ratios")
        print("=" * 70)
        
        # Load base config
        with open(self.config_path, 'r') as f:
            base_config = yaml.safe_load(f)
        
        # Generate parameter grid
        param_combinations = self.generate_parameter_grid()
        
        total_combinations = len(param_combinations)
        start_time = time.time()
        
        print(f"🔬 Testing {total_combinations} parameter combinations")
        print(f"⏱️  Estimated time: {total_combinations * 1:.1f} minutes")
        print()
        
        for i, params in enumerate(param_combinations):
            elapsed_time = time.time() - start_time
            avg_time_per_test = elapsed_time / (i + 1) if i > 0 else 60
            remaining_time = avg_time_per_test * (total_combinations - i - 1)
            
            print(f"🔍 [{i+1}/{total_combinations}] Testing:")
            print(f"   EMA: {params['ema_length']:2d}, EMA_Back: {params['ema_backcandles']:2d}")
            print(f"   HL_Back: {params['hl_backcandles']:2d}, TP_Mult: {params['tp_multiplier']:3.1f}")
            print(f"   SL: swing_low - {params['sl_tick_distance']:.2f}")
            print(f"   ⏱️  Elapsed: {elapsed_time/60:.1f}m, Est. Remaining: {remaining_time/60:.1f}m")
            
            # Create temporary config
            temp_config = self.create_modified_config(base_config, params)
            temp_config_path = f"temp_tight_stops_{i}.yaml"
            
            with open(temp_config_path, 'w') as f:
                yaml.dump(temp_config, f)
            
            # Run backtest
            result = self.run_backtest(params, temp_config_path)
            
            # Clean up
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)
            
            if result:
                self.results.append(result)
                
                # Track best results
                if result['win_rate'] > self.best_win_rate:
                    self.best_win_rate = result['win_rate']
                    self.best_params = params
                    print(f"   🎉 NEW BEST WIN RATE: {result['win_rate']:.2f}%!")
                
                if result['profit_factor'] > self.best_profit_factor:
                    self.best_profit_factor = result['profit_factor']
                
                print(f"   ✅ Trades: {result['total_trades']:3d}, Win Rate: {result['win_rate']:6.2f}%")
                print(f"   💰 PnL: ${result['total_pnl']:8.2f}, Profit Factor: {result['profit_factor']:5.2f}")
                print(f"   📊 Avg Win: ${result['avg_win']:6.2f}, Avg Loss: ${result['avg_loss']:6.2f}")
                print(f"   ⚖️  Avg R/R: {result['avg_rr_ratio']:4.2f}:1")
            else:
                print(f"   ❌ No valid results")
        
        # Final summary
        self.save_results()
        return self.best_params
    
    def save_results(self):
        """Save all optimization results"""
        if not self.results:
            print("❌ No results to save")
            return
        
        # Create results DataFrame
        results_df = pd.DataFrame(self.results)
        
        # Calculate composite score (weighted: 60% win rate, 40% profit factor)
        max_win_rate = results_df['win_rate'].max()
        max_profit_factor = results_df['profit_factor'].max()
        
        if max_win_rate > 0 and max_profit_factor > 0:
            results_df['composite_score'] = (
                0.6 * (results_df['win_rate'] / max_win_rate) +
                0.4 * (results_df['profit_factor'] / max_profit_factor)
            )
        
        # Sort by multiple criteria
        results_df = results_df.sort_values(['win_rate', 'profit_factor', 'total_pnl'], 
                                          ascending=[False, False, False])
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tight_stops_optimization_{timestamp}.csv"
        results_df.to_csv(filename, index=False)
        
        # Save best parameters
        best_filename = f"best_tight_stops_params_{timestamp}.json"
        with open(best_filename, 'w') as f:
            json.dump({
                'best_params': self.best_params,
                'best_win_rate': self.best_win_rate,
                'best_profit_factor': self.best_profit_factor,
                'total_tests': len(self.results),
                'timestamp': timestamp
            }, f, indent=2)
        
        print(f"\n💾 Results saved to {filename}")
        print(f"💾 Best parameters saved to {best_filename}")
        
        # Print comprehensive results
        self.print_results(results_df)
    
    def print_results(self, results_df, top_n=10):
        """Print optimization results"""
        print(f"\n🏆 TIGHT STOPS OPTIMIZATION RESULTS")
        print("=" * 100)
        
        top_results = results_df.head(top_n)
        
        print(f"\n📈 TOP {top_n} PARAMETER COMBINATIONS:")
        print("=" * 100)
        print("Rank | Win Rate | Profit Factor | Total PnL  | Trades | R/R Ratio | EMA | EMA_Back | HL_Back | TP_Mult")
        print("-" * 100)
        
        for i, (_, result) in enumerate(top_results.iterrows(), 1):
            print(f"{i:4d} | {result['win_rate']:7.2f}% | {result['profit_factor']:12.2f} | "
                  f"${result['total_pnl']:8.2f} | {result['total_trades']:6d} | "
                  f"{result['avg_rr_ratio']:8.2f}:1 | "
                  f"{result['params']['ema_length']:3d} | {result['params']['ema_backcandles']:8d} | "
                  f"{result['params']['hl_backcandles']:7d} | {result['params']['tp_multiplier']:6.1f}")
        
        # Statistical summary
        print(f"\n📊 STATISTICAL SUMMARY:")
        print(f"   Total Tests: {len(results_df)}")
        print(f"   Average Win Rate: {results_df['win_rate'].mean():.2f}%")
        print(f"   Max Win Rate: {results_df['win_rate'].max():.2f}%")
        print(f"   Average Profit Factor: {results_df['profit_factor'].mean():.2f}")
        print(f"   Max Profit Factor: {results_df['profit_factor'].max():.2f}")
        print(f"   Average R/R Ratio: {results_df['avg_rr_ratio'].mean():.2f}:1")
        
        # Best overall
        best_result = results_df.iloc[0]
        print(f"\n🎯 BEST OVERALL PARAMETERS:")
        print(f"   Win Rate: {best_result['win_rate']:.2f}%")
        print(f"   Profit Factor: {best_result['profit_factor']:.2f}")
        print(f"   Total PnL: ${best_result['total_pnl']:.2f}")
        print(f"   Average R/R: {best_result['avg_rr_ratio']:.2f}:1")
        print(f"   Parameters: {best_result['params']}")

def run_tight_stops_optimization():
    """Run the tight stops optimization"""
    print("🎯 TIGHT STOPS + IMPROVED R/R OPTIMIZATION")
    print("Testing: Swing_Low - 0.02 stops with TP multipliers 1.5-3.0")
    print("=" * 80)
    
    optimizer = TightStopsOptimizer()
    
    # Calculate total combinations
    total_combos = 2 * 2 * 2 * 1 * 4  # 32 combinations
    print(f"📊 TOTAL COMBINATIONS: {total_combos}")
    print(f"⏱️  ESTIMATED TIME: {total_combos * 1:.1f} minutes")
    print("🚀 Starting optimization...")
    
    best_params = optimizer.optimize()
    
    if best_params:
        print(f"\n🎉 OPTIMIZATION COMPLETED!")
        print(f"🏆 Best Parameters Found:")
        for key, value in best_params.items():
            print(f"   {key}: {value}")
        print(f"   Highest Win Rate: {optimizer.best_win_rate:.2f}%")
        print(f"   Best Profit Factor: {optimizer.best_profit_factor:.2f}")
    else:
        print("❌ No valid results found")

if __name__ == "__main__":
    run_tight_stops_optimization()