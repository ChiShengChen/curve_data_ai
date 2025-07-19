#!/usr/bin/env python3
"""
Curve智能重新平衡系统配置文件
"""

import os
from typing import Dict, List, Optional

class Config:
    """系统配置类"""
    
    # API配置
    API_KEYS = {
        # Web3提供商 (填入你的API密钥)
        'INFURA_API_KEY': os.getenv('INFURA_API_KEY', ''),
        'ALCHEMY_API_KEY': os.getenv('ALCHEMY_API_KEY', ''),
        'QUICKNODE_API_KEY': os.getenv('QUICKNODE_API_KEY', ''),
        
        # 可选的API密钥
        'COINGECKO_API_KEY': os.getenv('COINGECKO_API_KEY', ''),
        'DEFILLAMA_API_KEY': os.getenv('DEFILLAMA_API_KEY', ''),
    }
    
    # Web3提供商URL
    @classmethod
    def get_web3_provider_url(cls) -> Optional[str]:
        """获取Web3提供商URL"""
        if cls.API_KEYS['INFURA_API_KEY']:
            return f"https://mainnet.infura.io/v3/{cls.API_KEYS['INFURA_API_KEY']}"
        elif cls.API_KEYS['ALCHEMY_API_KEY']:
            return f"https://eth-mainnet.g.alchemy.com/v2/{cls.API_KEYS['ALCHEMY_API_KEY']}"
        elif cls.API_KEYS['QUICKNODE_API_KEY']:
            return f"https://eth-mainnet.g.alchemy.com/v2/{cls.API_KEYS['QUICKNODE_API_KEY']}"
        else:
            return None
    
    # Curve池配置
    CURVE_POOLS = {
        '3pool': {
            'address': '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
            'name': '3Pool',
            'tokens': ['USDC', 'USDT', 'DAI'],
            'decimals': [6, 6, 18],
            'description': 'USDC/USDT/DAI stablecoin pool'
        },
        'frax': {
            'address': '0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B',
            'name': 'FRAX',
            'tokens': ['FRAX', 'USDC'],
            'decimals': [18, 6],
            'description': 'FRAX/USDC pool'
        },
        'mim': {
            'address': '0x5a6A4D54456819C6Cd2fE4de20b59F4f5F3f9b2D',
            'name': 'MIM',
            'tokens': ['MIM', '3CRV'],
            'decimals': [18, 18],
            'description': 'Magic Internet Money pool'
        },
        'lusd': {
            'address': '0xEd279fDD11cA84bEef15AF5D39BB4d4bEE23F0cA',
            'name': 'LUSD',
            'tokens': ['LUSD', '3CRV'],
            'decimals': [18, 18],
            'description': 'Liquity USD pool'
        }
    }
    
    # 数据源配置
    DATA_SOURCES = {
        'curve_api': {
            'base_url': 'https://api.curve.fi',
            'enabled': True,
            'priority': 1,
            'timeout': 10
        },
        'the_graph': {
            'base_url': 'https://api.thegraph.com/subgraphs/name/messari/curve-finance-ethereum',
            'enabled': True,
            'priority': 2,
            'timeout': 15
        },
        'defillama': {
            'base_url': 'https://yields.llama.fi',
            'enabled': True,
            'priority': 3,
            'timeout': 10
        },
        'coingecko': {
            'base_url': 'https://api.coingecko.com/api/v3',
            'enabled': True,
            'priority': 4,
            'timeout': 10
        },
        'onchain': {
            'enabled': True,
            'priority': 5,
            'timeout': 30
        }
    }
    
    # 交易配置
    TRADING_CONFIG = {
        'min_profit_threshold': 0.001,  # 0.1%
        'max_risk_score': 0.7,
        'max_slippage': 0.005,  # 0.5%
        'min_confidence': 0.6,
        'max_trade_amount': 100000,  # $100k
        'cooldown_period': 300,  # 5分钟
    }
    
    # 模型配置
    MODEL_CONFIG = {
        'input_features': ['usdc_balance', 'usdt_balance', 'dai_balance', 'virtual_price', 'volume_24h'],
        'sequence_length': 24,
        'hidden_dim': 128,
        'num_layers': 2,
        'dropout_rate': 0.2,
        'learning_rate': 0.001
    }
    
    # 数据更新间隔（秒）
    UPDATE_INTERVALS = {
        'real_time_data': 60,        # 1分钟
        'historical_data': 3600,     # 1小时
        'model_prediction': 300,     # 5分钟
        'health_check': 600          # 10分钟
    }
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """验证配置"""
        results = {}
        
        # 检查API密钥
        has_web3_key = any([
            cls.API_KEYS['INFURA_API_KEY'],
            cls.API_KEYS['ALCHEMY_API_KEY'],
            cls.API_KEYS['QUICKNODE_API_KEY']
        ])
        results['has_web3_provider'] = has_web3_key
        
        # 检查配置完整性
        results['pools_configured'] = len(cls.CURVE_POOLS) > 0
        results['data_sources_configured'] = len(cls.DATA_SOURCES) > 0
        
        return results
    
    @classmethod
    def print_config_status(cls):
        """打印配置状态"""
        print("🔧 系统配置状态")
        print("=" * 40)
        
        validation = cls.validate_config()
        
        # Web3状态
        web3_url = cls.get_web3_provider_url()
        if web3_url:
            print(f"✅ Web3 Provider: {web3_url[:50]}...")
        else:
            print("⚠️  Web3 Provider: 未配置 (将使用模拟数据)")
        
        # 池配置
        print(f"✅ Curve Pools: {len(cls.CURVE_POOLS)} 个池子已配置")
        for key, pool in cls.CURVE_POOLS.items():
            print(f"   - {pool['name']}: {'/'.join(pool['tokens'])}")
        
        # 数据源
        enabled_sources = [name for name, config in cls.DATA_SOURCES.items() if config['enabled']]
        print(f"✅ Data Sources: {len(enabled_sources)} 个数据源已启用")
        print(f"   {', '.join(enabled_sources)}")
        
        print()

# 环境变量设置说明
ENV_SETUP_GUIDE = """
🔑 API密钥设置指南

1. 设置环境变量 (推荐):
   export INFURA_API_KEY="your_infura_key_here"
   export ALCHEMY_API_KEY="your_alchemy_key_here"
   export COINGECKO_API_KEY="your_coingecko_key_here"

2. 或创建 .env 文件:
   INFURA_API_KEY=your_infura_key_here
   ALCHEMY_API_KEY=your_alchemy_key_here
   
3. API密钥获取地址:
   - Infura: https://infura.io/
   - Alchemy: https://alchemy.com/
   - CoinGecko: https://www.coingecko.com/en/api

注意: 没有API密钥系统仍可运行，但会使用模拟数据
"""

if __name__ == "__main__":
    Config.print_config_status()
    print(ENV_SETUP_GUIDE) 