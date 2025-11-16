# vwap_ma_strategy/optimize_comprehensive.py
"""
Comprehensive Parameter Optimization for QQQ/SPY Scalping Strategy
Tests all combinations of specified parameter ranges
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

class ComprehensiveOptimizer:
    def __init__(self, config_path="config/vwap_ma_config.yaml"):
        self.config_path = config_path
        self.results = []
        self.best_win_rate = 0
        self.best_profit_factor = 0
        self.best_params = None
        
    def generate_parameter_grid(self):
        """Generate comprehensive parameter combinations based on your ranges"""
        parameter_grid = {
            'ema_length': [20, 30, 50, 100],
            'ema_backcandles': [7, 14, 21],
            'hl_backcandles': [7, 14, 21],
            'atr_multiplier': [1.0, 1.2, 1.5],
            'tp_multiplier': [1.0, 1.2, 1.5, 1.7, 2.0]
        }
        
        # Generate all combinations
        keys = parameter_grid.keys()
        values = parameter_grid.values()
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        total_combinations = len(combinations)
        print(f"🎯 GENERATED PARAMETER GRID:")
        print(f"   EMA Length: {parameter_grid['ema_length']}")
        print(f"   EMA Backcandles: {parameter_grid['ema_backcandles']}")
        print(f"   HL Backcandles: {parameter_grid['hl_backcandles']}")
        print(f"   ATR Multiplier: {parameter_grid['atr_multiplier']}")
        print(f"   TP Multiplier: {parameter_grid['tp_multiplier']}")
        print(f"   TOTAL COMBINATIONS: {total_combinations}")
        
        return combinations
    
    def create_modified_config(self, base_config, params):
        """Create modified config with current parameters"""
        modified_config = base_config.copy()
        modified_config['reversal_strategy'].update(params)
        return modified_config
    
    def run_backtest(self, params, temp_config_path):
        """Run backtest with given parameters"""
        try:
            cmd = [
                'python', 'main_reversal_detailed_with_analysis_fixed.py',
                '--config', temp_config_path,
                '--no-plot'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='.', timeout=180)
            
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
                
                # Calculate additional metrics
                avg_win = combined_trades[combined_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
                avg_loss = combined_trades[combined_trades['pnl'] < 0]['pnl'].mean() if (total_trades - winning_trades) > 0 else 0
                profit_per_trade = total_pnl / total_trades if total_trades > 0 else 0
                
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
                    'profit_per_trade': profit_per_trade,
                    'winning_trades': winning_trades,
                    'losing_trades': total_trades - winning_trades
                }
            return None
            
        except Exception as e:
            print(f"    ❌ Error parsing results: {e}")
            return None
    
    def optimize(self, max_combinations=None):
        """Run comprehensive optimization"""
        print("🚀 COMPREHENSIVE PARAMETER OPTIMIZATION")
        print("=" * 70)
        
        # Load base config
        with open(self.config_path, 'r') as f:
            base_config = yaml.safe_load(f)
        
        # Generate parameter grid
        param_combinations = self.generate_parameter_grid()
        
        if max_combinations:
            param_combinations = param_combinations[:max_combinations]
            print(f"🔬 Testing first {max_combinations} combinations")
        else:
            print(f"🔬 Testing ALL {len(param_combinations)} combinations")
        
        total_combinations = len(param_combinations)
        start_time = time.time()
        completed = 0
        
        print(f"\n📊 STARTING OPTIMIZATION...")
        print("=" * 70)
        
        for i, params in enumerate(param_combinations):
            completed += 1
            elapsed_time = time.time() - start_time
            avg_time_per_test = elapsed_time / completed if completed > 0 else 0
            remaining_time = avg_time_per_test * (total_combinations - completed)
            
            print(f"\n🔍 [{completed}/{total_combinations}] Testing:")
            print(f"   EMA: {params['ema_length']:3d}, EMA_Back: {params['ema_backcandles']:2d}")
            print(f"   HL_Back: {params['hl_backcandles']:2d}, ATR_Mult: {params['atr_multiplier']:3.1f}")
            print(f"   TP_Mult: {params['tp_multiplier']:3.1f}")
            print(f"   ⏱️  Elapsed: {elapsed_time/60:.1f}m, Est. Remaining: {remaining_time/60:.1f}m")
            
            # Create temporary config
            temp_config = self.create_modified_config(base_config, params)
            temp_config_path = f"temp_optimize_{i}.yaml"
            
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
        
        # Calculate composite score (weighted: 70% win rate, 30% profit factor)
        max_win_rate = results_df['win_rate'].max()
        max_profit_factor = results_df['profit_factor'].max()
        
        if max_win_rate > 0 and max_profit_factor > 0:
            results_df['composite_score'] = (
                0.7 * (results_df['win_rate'] / max_win_rate) +
                0.3 * (results_df['profit_factor'] / max_profit_factor)
            )
        
        # Sort by multiple criteria
        results_df = results_df.sort_values(['win_rate', 'profit_factor', 'total_pnl'], 
                                          ascending=[False, False, False])
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_optimization_{timestamp}.csv"
        results_df.to_csv(filename, index=False)
        
        # Save best parameters
        best_filename = f"best_parameters_comprehensive_{timestamp}.json"
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
        self.print_comprehensive_results(results_df)
    
    def print_comprehensive_results(self, results_df, top_n=20):
        """Print comprehensive results analysis"""
        print(f"\n🏆 COMPREHENSIVE OPTIMIZATION RESULTS")
        print("=" * 100)
        
        top_results = results_df.head(top_n)
        
        print(f"\n📈 TOP {top_n} PARAMETER COMBINATIONS:")
        print("=" * 100)
        print("Rank | Win Rate | Profit Factor | Total PnL  | Trades | EMA | EMA_Back | HL_Back | ATR_Mult | TP_Mult")
        print("-" * 100)
        
        for i, (_, result) in enumerate(top_results.iterrows(), 1):
            print(f"{i:4d} | {result['win_rate']:7.2f}% | {result['profit_factor']:12.2f} | "
                  f"${result['total_pnl']:8.2f} | {result['total_trades']:6d} | "
                  f"{result['params']['ema_length']:3d} | {result['params']['ema_backcandles']:8d} | "
                  f"{result['params']['hl_backcandles']:7d} | {result['params']['atr_multiplier']:8.1f} | "
                  f"{result['params']['tp_multiplier']:6.1f}")
        
        # Statistical summary
        print(f"\n📊 STATISTICAL SUMMARY:")
        print(f"   Total Tests: {len(results_df)}")
        print(f"   Average Win Rate: {results_df['win_rate'].mean():.2f}%")
        print(f"   Max Win Rate: {results_df['win_rate'].max():.2f}%")
        print(f"   Average Profit Factor: {results_df['profit_factor'].mean():.2f}")
        print(f"   Max Profit Factor: {results_df['profit_factor'].max():.2f}")
        print(f"   Average Total PnL: ${results_df['total_pnl'].mean():.2f}")
        
        # Best overall
        best_result = results_df.iloc[0]
        print(f"\n🎯 BEST OVERALL PARAMETERS:")
        print(f"   Win Rate: {best_result['win_rate']:.2f}%")
        print(f"   Profit Factor: {best_result['profit_factor']:.2f}")
        print(f"   Total PnL: ${best_result['total_pnl']:.2f}")
        print(f"   Parameters: {best_result['params']}")

def run_comprehensive_optimization(max_combinations=None):
    """Run the comprehensive optimization"""
    print("🎯 QQQ/SPY COMPREHENSIVE PARAMETER OPTIMIZATION")
    print("Testing: EMA[20,30,50,100] × EMA_Back[7,14,21] × HL_Back[7,14,21] × ATR_Mult[1.0,1.2,1.5] × TP_Mult[1.0,1.2,1.5,1.7,2.0]")
    print("=" * 80)
    
    optimizer = ComprehensiveOptimizer()
    
    # Calculate total combinations
    total_combos = 4 * 3 * 3 * 3 * 5  # 540 total combinations
    print(f"📊 TOTAL COMBINATIONS: {total_combos}")
    
    if max_combinations:
        print(f"🔬 TESTING: First {max_combinations} combinations")
        estimated_time = (max_combinations * 60) / 60  # ~60 seconds per test
    else:
        print(f"🔬 TESTING: All {total_combos} combinations")
        estimated_time = (total_combos * 60) / 3600  # Convert to hours
    
    print(f"⏱️  ESTIMATED TIME: {estimated_time:.1f} hours")
    print("🚀 Starting optimization...")
    
    best_params = optimizer.optimize(max_combinations=max_combinations)
    
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
    # For full optimization: remove max_combinations parameter
    # For testing: use max_combinations=10
    #run_comprehensive_optimization(max_combinations=10)
    run_comprehensive_optimization()