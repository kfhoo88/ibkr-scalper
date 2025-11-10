# create_proven_config.py
import yaml

def create_proven_config():
    """Create the proven configuration file"""
    proven_config = {
        'options': {
            'strike_selection': '1_OTM'
        },
        'strategy': {
            'ma_fast_period': 9,
            'ma_slow_period': 14,
            'min_volume': 1000,
            'max_volatility': 2.0,
            'avoid_open_minutes': 15,
            'avoid_close_minutes': 30,
            'max_hold_minutes': 20
        },
        'risk': {
            'stop_loss_pct': 30,
            'take_profit_pct': 20,
            'hedge_activation_pct': 20
        },
        'trading': {
            'max_position_value': 200
        },
        'backtesting': {
            'initial_capital': 10000
        }
    }
    
    with open('config/scalping_config_proven.yaml', 'w') as f:
        yaml.dump(proven_config, f, default_flow_style=False)
    
    print("CREATED: config/scalping_config_proven.yaml")
    print("Using proven parameters that gave 62% win rate")

if __name__ == "__main__":
    create_proven_config()