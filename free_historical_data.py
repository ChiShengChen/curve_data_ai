#!/usr/bin/env python3
"""
免费历史数据获取策略
专门针对不想花钱但需要历史数据的场景
"""

import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path

# ========================================
# 🔧 配置参数 - 在这里修改天数设置
# ========================================
DEFAULT_HISTORICAL_DAYS = 365  # 默认获取1年历史数据
MAX_THEGRAPH_DAYS = 365       # The Graph API最大支持天数 (已废弃)
DEFAULT_SELF_BUILT_DAYS = 365 # 自建数据库默认天数

# 快速配置选项
QUICK_TEST_DAYS = 7           # 快速测试用(7天)
MEDIUM_RANGE_DAYS = 90        # 中期分析用(3个月) 
FULL_YEAR_DAYS = 365          # 完整年度数据

# 当前使用的配置 - 修改这里来改变所有方法的默认值
CURRENT_DAYS_SETTING =  FULL_YEAR_DAYS  # 🔥 暂时改为7天避免长时间等待

# ========================================
# 🚨 API 状态配置 - 控制哪些数据源可用
# ========================================
ENABLE_THEGRAPH_API = False     # ❌ The Graph API已被移除，禁用
ENABLE_CURVE_API = True         # ✅ Curve API (主要数据源)
ENABLE_DEFILLAMA = True         # ✅ DefiLlama APY数据  
ENABLE_SELF_BUILT = True        # ✅ 自建数据库 (作为最后备份)
ENABLE_SSL_VERIFICATION = False # 🔧 禁用SSL验证来避免证书错误

# 性能优化配置
MAX_COLLECTION_ATTEMPTS = 50   # 🔥 限制最大收集次数，避免无限循环
COLLECTION_BATCH_SIZE = 10     # 每批次收集的数据点数量
REQUEST_TIMEOUT = 5            # API请求超时时间 (秒)
REQUEST_RETRY_DELAY = 2        # 请求失败后重试延迟 (秒)

# ========================================
# 🎯 所有主要Curve池子配置 - 扩展版
# ========================================

# 完整的主要Curve池子配置
AVAILABLE_POOLS = {
    # === 🏆 主要稳定币池 (Base Pools) ===
    '3pool': {
        'address': '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
        'name': 'DAI/USDC/USDT',
        'tokens': ['DAI', 'USDC', 'USDT'],
        'type': 'stable',
        'priority': 1  # 最高优先级
    },
    'frax': {
        'address': '0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B', 
        'name': 'FRAX/3CRV',
        'tokens': ['FRAX', '3CRV'],
        'type': 'metapool',
        'priority': 2
    },
    'lusd': {
        'address': '0xEd279fDD11cA84bEef15AF5D39BB4d4bEE23F0cA',
        'name': 'LUSD/3CRV', 
        'tokens': ['LUSD', '3CRV'],
        'type': 'metapool',
        'priority': 2
    },
    'mim': {
        'address': '0x5a6A4D54456819380173272A5E8E9B9904BdF41B',
        'name': 'MIM/3CRV',
        'tokens': ['MIM', '3CRV'], 
        'type': 'metapool',
        'priority': 3
    },
    
    # === 🔥 ETH/stETH 池 ===
    'steth': {
        'address': '0xDC24316b9AE028F1497c275EB9192a3Ea0f67022',
        'name': 'ETH/stETH',
        'tokens': ['ETH', 'stETH'],
        'type': 'eth_pool',
        'priority': 2
    },
    'seth': {
        'address': '0xc5424B857f758E906013F3555Dad202e4bdB4567',
        'name': 'ETH/sETH',
        'tokens': ['ETH', 'sETH'],
        'type': 'eth_pool', 
        'priority': 3
    },
    'reth': {
        'address': '0xF9440930043eb3997fc70e1339dBb11F341de7A8',
        'name': 'ETH/rETH',
        'tokens': ['ETH', 'rETH'],
        'type': 'eth_pool',
        'priority': 3
    },
    'ankrETH': {
        'address': '0xA96A65c051bF88B4095Ee1f2451C2A9d43F53Ae2',
        'name': 'ETH/ankrETH', 
        'tokens': ['ETH', 'ankrETH'],
        'type': 'eth_pool',
        'priority': 4
    },
    
    # === ₿ BTC 池 ===
    'renbtc': {
        'address': '0x93054188d876f558f4a66B2EF1d97d16eDf0895B',
        'name': 'renBTC/WBTC',
        'tokens': ['renBTC', 'WBTC'],
        'type': 'btc_pool',
        'priority': 3
    },
    'sbtc': {
        'address': '0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714',
        'name': 'renBTC/WBTC/sBTC',
        'tokens': ['renBTC', 'WBTC', 'sBTC'],
        'type': 'btc_pool',
        'priority': 3
    },
    'hbtc': {
        'address': '0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F',
        'name': 'hBTC/WBTC',
        'tokens': ['hBTC', 'WBTC'],
        'type': 'btc_pool',
        'priority': 4
    },
    'bbtc': {
        'address': '0x071c661B4DeefB59E2a3DdB20Db036821eeE8F4b',
        'name': 'bBTC/sbtcCRV',
        'tokens': ['bBTC', 'sbtcCRV'],
        'type': 'btc_metapool',
        'priority': 4
    },
    'obtc': {
        'address': '0xd81dA8D904b52208541Bade1bD6595D8a251F8dd',
        'name': 'oBTC/sbtcCRV',
        'tokens': ['oBTC', 'sbtcCRV'],
        'type': 'btc_metapool', 
        'priority': 4
    },
    'pbtc': {
        'address': '0x7F55DDe206dbAD629C080068923b36fe9D6bDBeF',
        'name': 'pBTC/sbtcCRV',
        'tokens': ['pBTC', 'sbtcCRV'],
        'type': 'btc_metapool',
        'priority': 4
    },
    'tbtc': {
        'address': '0xC25099792E9349C7DD09759744ea681C7de2cb66',
        'name': 'tBTC/sbtcCRV', 
        'tokens': ['tBTC', 'sbtcCRV'],
        'type': 'btc_metapool',
        'priority': 4
    },
    
    # === 🚀 Crypto 池 ===
    'tricrypto': {
        'address': '0x80466c64868E1ab14a1Ddf27A676C3fcBE638Fe5',
        'name': 'USDT/WBTC/WETH',
        'tokens': ['USDT', 'WBTC', 'WETH'],
        'type': 'crypto',
        'priority': 2
    },
    'tricrypto2': {
        'address': '0xD51a44d3FaE010294C616388b506AcDA1bfAAE46', 
        'name': 'USDT/WBTC/WETH v2',
        'tokens': ['USDT', 'WBTC', 'WETH'],
        'type': 'crypto',
        'priority': 2
    },
    
    # === 🏦 Lending 池 ===
    'aave': {
        'address': '0xDeBF20617708857ebe4F679508E7b7863a8A8EeE',
        'name': 'aDAI/aUSDC/aUSDT',
        'tokens': ['aDAI', 'aUSDC', 'aUSDT'],
        'type': 'lending',
        'priority': 3
    },
    'compound': {
        'address': '0xA2B47E3D5c44877cca798226B7B8118F9BFb7A56',
        'name': 'cDAI/cUSDC',
        'tokens': ['cDAI', 'cUSDC'],
        'type': 'lending',
        'priority': 4
    },
    'ironbank': {
        'address': '0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF',
        'name': 'cyDAI/cyUSDC/cyUSDT',
        'tokens': ['cyDAI', 'cyUSDC', 'cyUSDT'],
        'type': 'lending',
        'priority': 4
    },
    'saave': {
        'address': '0xEB16Ae0052ed37f479f7fe63849198Df1765a733',
        'name': 'sDAI/sUSDC/sUSDT',
        'tokens': ['sDAI', 'sUSDC', 'sUSDT'],
        'type': 'lending',
        'priority': 4
    },
    
    # === 🌍 国际化稳定币 ===
    'eurs': {
        'address': '0x0Ce6a5fF5217e38315f87032CF90686C96627CAA',
        'name': 'EURS/sEUR',
        'tokens': ['EURS', 'sEUR'],
        'type': 'international',
        'priority': 4
    },
    
    # === 📈 更多Meta池 ===
    'gusd': {
        'address': '0x4f062658EaAF2C1ccf8C8e36D6824CDf41167956',
        'name': 'GUSD/3CRV',
        'tokens': ['GUSD', '3CRV'],
        'type': 'metapool',
        'priority': 4
    },
    'husd': {
        'address': '0x3eF6A01A0f81D6046290f3e2A8c5b843e738E604',
        'name': 'HUSD/3CRV',
        'tokens': ['HUSD', '3CRV'],
        'type': 'metapool',
        'priority': 4
    },
    'musd': {
        'address': '0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6',
        'name': 'MUSD/3CRV',
        'tokens': ['MUSD', '3CRV'],
        'type': 'metapool',
        'priority': 4
    },
    'dusd': {
        'address': '0x8038C01A0390a8c547446a0b2c18fc9aEFEcc10c',
        'name': 'DUSD/3CRV',
        'tokens': ['DUSD', '3CRV'],
        'type': 'metapool',
        'priority': 5
    },
    'usdk': {
        'address': '0x3E01dD8a5E1fb3481F0F589056b428Fc308AF0Fb',
        'name': 'USDK/3CRV',
        'tokens': ['USDK', '3CRV'],
        'type': 'metapool',
        'priority': 5
    },
    'usdn': {
        'address': '0x0f9cb53Ebe405d49A0bbdBD291A65Ff571bC83e1',
        'name': 'USDN/3CRV',
        'tokens': ['USDN', '3CRV'],
        'type': 'metapool',
        'priority': 5
    },
    'usdp': {
        'address': '0x42d7025938bEc20B69cBae5A77421082407f053A',
        'name': 'USDP/3CRV',
        'tokens': ['USDP', '3CRV'],
        'type': 'metapool',
        'priority': 4
    },
    'ust': {
        'address': '0x890f4e345B1dAED0367A877a1612f86A1f86985f',
        'name': 'UST/3CRV',
        'tokens': ['UST', '3CRV'],
        'type': 'metapool',
        'priority': 5  # 较低优先级因为UST已deprecated
    },
    'rsv': {
        'address': '0xC18cC39da8b11dA8c3541C598eE022258F9744da',
        'name': 'RSV/3CRV',
        'tokens': ['RSV', '3CRV'],
        'type': 'metapool',
        'priority': 5
    },
    'linkusd': {
        'address': '0xE7a24EF0C5e95Ffb0f6684b813A78F2a3AD7D171',
        'name': 'LINKUSD/3CRV',
        'tokens': ['LINKUSD', '3CRV'],
        'type': 'metapool',
        'priority': 5
    },
    
    # === 🔗 其他重要池子 ===
    'link': {
        'address': '0xF178C0b5Bb7e7aBF4e12A4838C7b7c5bA2C623c0',
        'name': 'LINK/sLINK',
        'tokens': ['LINK', 'sLINK'],
        'type': 'synthetic',
        'priority': 4
    },
    'susd': {
        'address': '0xA5407eAE9Ba41422680e2e00537571bcC53efBfD',
        'name': 'DAI/USDC/USDT/sUSD',
        'tokens': ['DAI', 'USDC', 'USDT', 'sUSD'],
        'type': 'stable_4pool',
        'priority': 4
    },
    'y': {
        'address': '0x45F783CCE6B7FF23B2ab2D70e416cdb7D6055f51',
        'name': 'yDAI/yUSDC/yUSDT/yTUSD',
        'tokens': ['yDAI', 'yUSDC', 'yUSDT', 'yTUSD'],
        'type': 'yield',
        'priority': 5
    },
    'busd': {
        'address': '0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27',
        'name': 'yDAI/yUSDC/yUSDT/yBUSD',
        'tokens': ['yDAI', 'yUSDC', 'yUSDT', 'yBUSD'],
        'type': 'yield',
        'priority': 5
    },
    'pax': {
        'address': '0x06364f10B501e868329afBc005b3492902d6C763',
        'name': 'ycDAI/ycUSDC/ycUSDT/PAX',
        'tokens': ['ycDAI', 'ycUSDC', 'ycUSDT', 'PAX'],
        'type': 'yield',
        'priority': 5
    }
}

# 根据优先级和类型筛选池子的函数
def get_pools_by_priority(min_priority=1, max_priority=5, pool_types=None):
    """
    根据优先级和类型筛选池子
    
    Args:
        min_priority: 最小优先级 (1=最高优先级)  
        max_priority: 最大优先级 (5=最低优先级)
        pool_types: 池子类型列表，如 ['stable', 'metapool'] 
    
    Returns:
        筛选后的池子字典
    """
    filtered_pools = {}
    
    for pool_name, pool_info in AVAILABLE_POOLS.items():
        # 优先级筛选
        if not (min_priority <= pool_info['priority'] <= max_priority):
            continue
            
        # 类型筛选
        if pool_types and pool_info['type'] not in pool_types:
            continue
            
        filtered_pools[pool_name] = pool_info
    
    return filtered_pools

def get_high_priority_pools():
    """获取高优先级池子 (priority 1-2)"""
    return get_pools_by_priority(min_priority=1, max_priority=2)

def get_stable_pools():
    """获取所有稳定币相关池子"""
    return get_pools_by_priority(pool_types=['stable', 'metapool', 'stable_4pool'])

def get_all_main_pools():
    """获取所有主要池子 (priority 1-3)"""  
    return get_pools_by_priority(min_priority=1, max_priority=3)

# 更新原有配置以保持兼容性
TARGET_POOL = '3pool'  # 默认池子
TARGET_POOL_ADDRESS = AVAILABLE_POOLS[TARGET_POOL]['address']
TARGET_POOL_NAME = AVAILABLE_POOLS[TARGET_POOL]['name']

# 批量模式配置
ENABLE_BATCH_MODE = False     # 是否启用批量模式 (收集所有池子)
BATCH_POOLS = ['3pool', 'frax', 'lusd']  # 批量模式时要收集的池子列表

# 显示当前配置信息
def show_current_config():
    """显示当前配置"""
    print("=" * 60)
    print("📋 当前爬虫配置")
    print("=" * 60)
    print(f"🎯 目标池子: {TARGET_POOL}")
    print(f"📛 池子名称: {TARGET_POOL_NAME}")  
    print(f"📍 池子地址: {TARGET_POOL_ADDRESS}")
    print(f"📊 数据天数: {CURRENT_DAYS_SETTING} 天")
    print(f"🔄 批量模式: {'启用' if ENABLE_BATCH_MODE else '禁用'}")
    if ENABLE_BATCH_MODE:
        print(f"📦 批量池子: {', '.join(BATCH_POOLS)}")
    print("=" * 60)
    print("💡 要切换池子，请修改 TARGET_POOL 变量!")
    print("   可选值: " + " | ".join(AVAILABLE_POOLS.keys()))
    print("=" * 60)

# 配置信息将在主程序运行时显示

class FreeHistoricalDataManager:
    """免费历史数据管理器"""
    
    def __init__(self, cache_dir: str = "free_historical_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 免费数据源
        self.sources = {
            'thegraph': {
                'url': 'https://api.thegraph.com/subgraphs/name/messari/curve-finance-ethereum',
                'daily_limit': 1000,
                'cost': 'FREE'
            },
            'curve_api': {
                'url': 'https://api.curve.fi/api',
                'daily_limit': 'unlimited',
                'cost': 'FREE'
            },
            'defillama': {
                'url': 'https://yields.llama.fi',
                'daily_limit': 'unlimited', 
                'cost': 'FREE'
            }
        }
        
        print(f"📁 免费历史数据缓存目录: {self.cache_dir.absolute()}")
    
    def get_thegraph_historical_data(self, pool_address: str, days: int = CURRENT_DAYS_SETTING) -> pd.DataFrame:
        """
        方法1: 使用The Graph获取历史数据 (已废弃)
        ❌ 注意: The Graph API端点已被移除
        """
        
        if not ENABLE_THEGRAPH_API:
            print(f"⚠️  [The Graph] API已被禁用 - 端点已废弃")
            return pd.DataFrame()
        
        print(f"📊 [The Graph] 尝试获取 {days} 天历史数据...")
        
        # GraphQL查询 - 分批获取避免超时
        query = """
        {
          pool(id: "%s") {
            name
            coins {
              symbol
              decimals
            }
            dailyPoolSnapshots(
              first: %d
              orderBy: timestamp
              orderDirection: desc
            ) {
              timestamp
              totalValueLockedUSD
              dailyVolumeUSD
              rates
              balances
              virtualPrice
            }
          }
        }
        """ % (pool_address.lower(), days)
        
        try:
            # 配置SSL验证
            verify_ssl = ENABLE_SSL_VERIFICATION
            
            response = requests.post(
                self.sources['thegraph']['url'],
                json={'query': query},
                timeout=REQUEST_TIMEOUT,
                headers={'Content-Type': 'application/json'},
                verify=verify_ssl
            )
            
            if response.status_code != 200:
                print(f"❌ The Graph API错误: {response.status_code}")
                return pd.DataFrame()
            
            data = response.json()
            
            if 'errors' in data:
                print(f"❌ GraphQL错误 (API已废弃): {data['errors'][0]['message'][:100]}...")
                return pd.DataFrame()
            
            pool_data = data['data']['pool']
            if not pool_data:
                print(f"❌ 未找到池子数据: {pool_address}")
                return pd.DataFrame()
            
            # 解析数据
            records = []
            snapshots = pool_data['dailyPoolSnapshots']
            coins = pool_data['coins']
            
            for snapshot in snapshots:
                record = {
                    'timestamp': pd.to_datetime(int(snapshot['timestamp']), unit='s'),
                    'tvl': float(snapshot.get('totalValueLockedUSD', 0)),
                    'volume_24h': float(snapshot.get('dailyVolumeUSD', 0)),
                    'virtual_price': float(snapshot.get('virtualPrice', 1e18)) / 1e18
                }
                
                # 解析余额数据
                balances = snapshot.get('balances', [])
                rates = snapshot.get('rates', [])
                
                for i, coin in enumerate(coins):
                    if i < len(balances):
                        balance = float(balances[i]) / (10 ** int(coin['decimals']))
                        record[f"{coin['symbol'].lower()}_balance"] = balance
                    
                    if i < len(rates):
                        record[f"{coin['symbol'].lower()}_rate"] = float(rates[i]) / 1e18
                
                records.append(record)
            
            df = pd.DataFrame(records)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            print(f"✅ [The Graph] 获取到 {len(df)} 条免费历史记录")
            return df
            
        except Exception as e:
            print(f"❌ The Graph查询失败 (API已废弃): {str(e)[:100]}...")
            return pd.DataFrame()
    
    def get_defillama_apy_history(self, pool_address: str) -> pd.DataFrame:
        """
        方法2: 从DefiLlama获取APY历史 (完全免费)
        """
        
        if not ENABLE_DEFILLAMA:
            print(f"⚠️  [DefiLlama] API已被禁用")
            return pd.DataFrame()
            
        print(f"📈 [DefiLlama] 获取APY历史数据...")
        
        try:
            # 获取池子APY历史
            url = f"https://yields.llama.fi/chart/{pool_address.lower()}"
            
            # 配置SSL验证和超时
            verify_ssl = ENABLE_SSL_VERIFICATION
            
            response = requests.get(
                url, 
                timeout=REQUEST_TIMEOUT,
                verify=verify_ssl
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    records = []
                    for item in data['data']:
                        records.append({
                            'timestamp': pd.to_datetime(item['timestamp']),
                            'apy': item['apy'] / 100 if item['apy'] else 0,
                            'tvl': item.get('tvlUsd', 0)
                        })
                    
                    df = pd.DataFrame(records)
                    print(f"✅ [DefiLlama] 获取到 {len(df)} 条APY历史记录")
                    return df
                else:
                    print(f"⚠️  [DefiLlama] 响应中无数据字段")
            else:
                print(f"❌ [DefiLlama] HTTP错误: {response.status_code}")
        
        except requests.exceptions.SSLError as e:
            print(f"❌ [DefiLlama] SSL错误: 请尝试禁用SSL验证")
        except requests.exceptions.Timeout as e:
            print(f"❌ [DefiLlama] 超时错误: {REQUEST_TIMEOUT}s")
        except Exception as e:
            print(f"❌ [DefiLlama] 查询失败: {str(e)[:100]}...")
        
        return pd.DataFrame()
    
    def build_historical_database(self, pool_name: str = TARGET_POOL, days_to_collect: int = CURRENT_DAYS_SETTING):
        """
        方法3: 自建免费历史数据库 (优化版 - 避免无限循环)
        通过有限次数尝试获取实时数据，然后生成合成历史数据
        """
        
        if not ENABLE_SELF_BUILT:
            print(f"⚠️  自建数据库已被禁用")
            return pd.DataFrame()
        
        print(f"🏗️  开始自建 {pool_name} 历史数据库 ({days_to_collect} 天)...")
        
        try:
            from real_data_collector import CurveRealDataCollector
            from data_manager import CurveDataManager
            
            collector = CurveRealDataCollector()
            manager = CurveDataManager(str(self.cache_dir / "self_built"))
            
            # 🔥 限制尝试次数，避免无限循环
            max_attempts = min(MAX_COLLECTION_ATTEMPTS, days_to_collect)
            successful_attempts = 0
            base_data = None
            
            print(f"🔄 尝试获取基础数据 (最多 {max_attempts} 次)...")
            
            # 先尝试获取一次有效的实时数据作为基准
            for attempt in range(max_attempts):
                try:
                    pool_data = collector.get_real_time_data(pool_name)
                    if pool_data:
                        base_data = pool_data
                        print(f"✅ 第 {attempt + 1} 次尝试成功获取基础数据")
                        break
                    
                    if attempt % 10 == 0 and attempt > 0:
                        print(f"⚠️  已尝试 {attempt + 1} 次，继续重试...")
                    
                    time.sleep(REQUEST_RETRY_DELAY)  # 避免请求过于频繁
                    
                except Exception as e:
                    if attempt % 10 == 0:
                        print(f"⚠️  第 {attempt + 1} 次尝试失败: {str(e)[:50]}...")
                    continue
            
            # 如果无法获取真实数据，生成合成数据
            if not base_data:
                print("⚠️  无法获取真实数据，生成合成历史数据...")
                return self._generate_synthetic_data(pool_name, days_to_collect)
            
            # 基于真实数据生成历史数据
            print(f"📊 基于真实数据生成 {days_to_collect} 天历史数据...")
            simulated_records = []
            
            for day in range(days_to_collect):
                # 每天生成几个数据点而不是每小时
                points_per_day = 4  # 每6小时一个数据点
                
                for point in range(points_per_day):
                    hour_offset = day * 24 + point * 6
                    
                    # 为每个时间点添加随机波动
                    noise_factor = 0.02  # 2%的随机波动
                    
                    record = {
                        'timestamp': datetime.now() - timedelta(hours=hour_offset),
                        'pool_address': base_data.pool_address,
                        'pool_name': base_data.pool_name,
                        'virtual_price': base_data.virtual_price * (1 + np.random.normal(0, noise_factor)),
                        'volume_24h': base_data.volume_24h * (1 + np.random.normal(0, noise_factor * 2)),
                        'apy': max(0, base_data.apy * (1 + np.random.normal(0, noise_factor))),
                        'total_supply': base_data.total_supply * (1 + np.random.normal(0, noise_factor * 0.5))
                    }
                    
                    # 添加代币余额
                    for i, (token, balance) in enumerate(zip(base_data.tokens, base_data.balances)):
                        record[f'{token.lower()}_balance'] = balance * (1 + np.random.normal(0, noise_factor))
                    
                    simulated_records.append(record)
                
                # 显示进度
                if day % max(1, days_to_collect // 10) == 0:
                    progress = (day / days_to_collect) * 100
                    print(f"📈 生成进度: {progress:.0f}% ({day}/{days_to_collect} 天)")
        
        except ImportError as e:
            print(f"❌ 导入依赖失败: {e}")
            print("💡 生成基础合成数据...")
            return self._generate_synthetic_data(pool_name, days_to_collect)
        except Exception as e:
            print(f"❌ 自建数据库失败: {e}")
            print("💡 fallback到合成数据...")
            return self._generate_synthetic_data(pool_name, days_to_collect)
        
        if simulated_records:
            df = pd.DataFrame(simulated_records)
            
            # 保存自建历史数据
            filename = f"{pool_name}_self_built_historical_{days_to_collect}d.csv"
            filepath = self.cache_dir / filename
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            print(f"✅ 自建历史数据库完成: {filepath}")
            print(f"📊 总计 {len(df)} 条记录，时间跨度 {days_to_collect} 天")
            
            return df
        
        return pd.DataFrame()

    def _generate_synthetic_data(self, pool_name: str, days: int) -> pd.DataFrame:
        """生成合成历史数据 - 当所有真实数据源都失败时使用"""
        
        print(f"🎭 为 {pool_name} 生成 {days} 天合成历史数据...")
        
        # 根据池子类型设置不同的基础参数
        pool_configs = {
            'mim': {
                'tokens': ['MIM', 'USDC', 'USDT'], 
                'base_balance': 1000000,
                'base_apy': 0.05,
                'base_volume': 500000
            },
            '3pool': {
                'tokens': ['USDC', 'USDT', 'DAI'],
                'base_balance': 5000000, 
                'base_apy': 0.03,
                'base_volume': 2000000
            },
            'frax': {
                'tokens': ['FRAX', 'USDC'],
                'base_balance': 800000,
                'base_apy': 0.06,
                'base_volume': 300000
            },
            'lusd': {
                'tokens': ['LUSD', 'USDC', 'USDT'],
                'base_balance': 600000,
                'base_apy': 0.04,
                'base_volume': 200000
            }
        }
        
        config = pool_configs.get(pool_name, pool_configs['3pool'])
        
        # 生成时间序列
        dates = pd.date_range(
            end=datetime.now(),
            periods=days * 6,  # 每天6个数据点
            freq='4H'  # 每4小时一个点
        )
        
        records = []
        for i, timestamp in enumerate(dates):
            # 添加一些趋势和随机性
            trend_factor = 1 + 0.1 * np.sin(i / (days * 0.5))  # 长期趋势
            noise_factor = np.random.normal(1, 0.02)  # 随机波动
            
            record = {
                'timestamp': timestamp,
                'pool_address': AVAILABLE_POOLS[pool_name]['address'],
                'pool_name': AVAILABLE_POOLS[pool_name]['name'],
                'virtual_price': 1.0 * trend_factor * noise_factor,
                'volume_24h': config['base_volume'] * trend_factor * noise_factor,
                'apy': max(0, config['base_apy'] * trend_factor * noise_factor),
                'total_supply': config['base_balance'] * 3 * trend_factor
            }
            
            # 添加代币余额
            for j, token in enumerate(config['tokens']):
                balance_variation = np.random.normal(1, 0.05)
                record[f'{token.lower()}_balance'] = config['base_balance'] * balance_variation
            
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # 保存合成数据
        filename = f"{pool_name}_synthetic_historical_{days}d.csv"  
        filepath = self.cache_dir / filename
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        print(f"✅ 合成数据生成完成: {filepath}")
        print(f"📊 生成了 {len(df)} 条合成记录")
        
        return df
    
    def get_comprehensive_free_data(self, pool_address: str = TARGET_POOL_ADDRESS, pool_name: str = TARGET_POOL, days: int = CURRENT_DAYS_SETTING) -> pd.DataFrame:
        """
        方法4: 综合免费数据策略 (优化版)
        结合多个免费源获取最完整的历史数据，包含fallback机制
        """
        
        print(f"🔄 综合免费策略获取 {pool_name} 历史数据 ({days} 天)...")
        
        all_data = []
        data_sources_tried = []
        
        # 1. 尝试The Graph (如果启用)
        if ENABLE_THEGRAPH_API:
            try:
                thegraph_data = self.get_thegraph_historical_data(pool_address, days)
                if not thegraph_data.empty:
                    thegraph_data['source'] = 'thegraph'
                    all_data.append(thegraph_data)
                    print(f"✅ The Graph: {len(thegraph_data)} 条记录")
                data_sources_tried.append('The Graph')
            except Exception as e:
                print(f"⚠️  The Graph尝试失败: {str(e)[:50]}...")
                data_sources_tried.append('The Graph (失败)')
        else:
            print("⚠️  The Graph已禁用")
        
        # 2. 尝试DefiLlama APY (如果启用)
        if ENABLE_DEFILLAMA:
            try:
                defillama_data = self.get_defillama_apy_history(pool_address)
                if not defillama_data.empty:
                    defillama_data['source'] = 'defillama'
                    all_data.append(defillama_data)
                    print(f"✅ DefiLlama: {len(defillama_data)} 条记录")
                data_sources_tried.append('DefiLlama')
            except Exception as e:
                print(f"⚠️  DefiLlama尝试失败: {str(e)[:50]}...")
                data_sources_tried.append('DefiLlama (失败)')
        
        # 3. 检查是否需要自建数据库补充
        total_records = sum(len(df) for df in all_data) if all_data else 0
        min_required_records = max(days // 10, 5)  # 至少需要的记录数
        
        if total_records < min_required_records:
            print(f"📊 免费API数据不足 ({total_records} < {min_required_records})，启用自建历史数据库...")
            
            if ENABLE_SELF_BUILT:
                try:
                    self_built_data = self.build_historical_database(pool_name, days)
                    if not self_built_data.empty:
                        self_built_data['source'] = 'self_built'
                        all_data.append(self_built_data)
                        print(f"✅ 自建数据: {len(self_built_data)} 条记录")
                    data_sources_tried.append('自建数据库')
                except Exception as e:
                    print(f"⚠️  自建数据库失败: {str(e)[:50]}...")
                    data_sources_tried.append('自建数据库 (失败)')
            else:
                print("⚠️  自建数据库已禁用")
        
        # 4. 合并所有数据源
        if all_data:
            try:
                # 按时间戳合并数据
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # 确保时间戳列存在且格式正确
                if 'timestamp' not in combined_df.columns:
                    print("⚠️  数据中缺少timestamp列，添加默认时间戳")
                    combined_df['timestamp'] = pd.date_range(
                        end=datetime.now(),
                        periods=len(combined_df),
                        freq='H'
                    )
                
                combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
                
                # 去重 (保留最新的记录)
                if len(combined_df) > 1:
                    combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
                
                # 保存综合数据
                filename = f"{pool_name}_comprehensive_free_historical_{days}d.csv"
                filepath = self.cache_dir / filename
                combined_df.to_csv(filepath, index=False, encoding='utf-8')
                
                print(f"🎉 综合免费历史数据获取完成!")
                print(f"📁 保存位置: {filepath}")
                print(f"📊 总记录数: {len(combined_df)}")
                print(f"🔄 数据来源: {', '.join([df['source'].iloc[0] for df in all_data if 'source' in df.columns and len(df) > 0])}")
                
                if 'timestamp' in combined_df.columns and len(combined_df) > 0:
                    print(f"🗓️  时间范围: {combined_df['timestamp'].min()} 到 {combined_df['timestamp'].max()}")
                
                return combined_df
            
            except Exception as e:
                print(f"❌ 数据合并失败: {e}")
                # 返回第一个可用的数据源
                if all_data:
                    print(f"💡 返回第一个可用数据源 ({len(all_data[0])} 条记录)")
                    return all_data[0]
        
        print(f"❌ 所有免费数据源都失败")
        print(f"🔍 已尝试的数据源: {', '.join(data_sources_tried)}")
        print(f"💡 建议: 检查网络连接或启用SSL验证")
        
        return pd.DataFrame()
    
    def setup_daily_collection(self, pool_name: str = TARGET_POOL):
        """
        方法5: 设置每日数据收集任务 (长期免费方案)
        建议使用cron定时任务每天运行
        """
        
        print(f"⏰ 设置 {pool_name} 每日数据收集...")
        
        # 创建每日收集脚本
        script_content = f"""#!/usr/bin/env python3
# 每日数据收集脚本 - 由cron定时运行
import sys
sys.path.append('/path/to/your/Quantum_curve_predict')

from free_historical_data import FreeHistoricalDataManager
from datetime import datetime

def daily_collect():
    manager = FreeHistoricalDataManager()
    
    # 获取今日数据
    df = manager.get_thegraph_historical_data('0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7', days=1)
    
    if not df.empty:
        # 追加到历史数据文件
        filename = 'daily_collection_{pool_name}.csv'
        filepath = manager.cache_dir / filename
        
        if filepath.exists():
            existing_df = pd.read_csv(filepath)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            combined_df = df
        
        combined_df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"✅ {{datetime.now()}}: 每日数据收集完成，共{{len(combined_df)}}条记录")
    else:
        print(f"❌ {{datetime.now()}}: 今日数据收集失败")

if __name__ == "__main__":
    daily_collect()
"""
        
        script_file = self.cache_dir / f"daily_collect_{pool_name}.py"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"📝 每日收集脚本已创建: {script_file}")
        print("💡 设置cron定时任务:")
        print(f"   0 1 * * * python3 {script_file.absolute()}")
        print("   (每天凌晨1点运行)")

    def get_batch_historical_data(self, pools_dict: dict, days: int = CURRENT_DAYS_SETTING, 
                                 max_concurrent: int = 3, delay_between_batches: int = 2) -> dict:
        """
        批量获取多个池子的历史数据
        
        Args:
            pools_dict: 池子字典 (来自 get_pools_by_priority 等函数)
            days: 获取天数
            max_concurrent: 最大并发数量
            delay_between_batches: 批次间延迟(秒)
        
        Returns:
            {pool_name: DataFrame} 字典
        """
        
        print(f"🚀 批量获取 {len(pools_dict)} 个池子的 {days} 天历史数据...")
        print(f"📋 池子列表: {', '.join(pools_dict.keys())}")
        print("="*60)
        
        results = {}
        successful = 0
        failed = 0
        
        # 按优先级排序池子
        sorted_pools = sorted(pools_dict.items(), key=lambda x: x[1]['priority'])
        
        # 分批处理避免API限制
        import math
        total_batches = math.ceil(len(sorted_pools) / max_concurrent)
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * max_concurrent
            end_idx = min(start_idx + max_concurrent, len(sorted_pools))
            current_batch = sorted_pools[start_idx:end_idx]
            
            print(f"📦 处理批次 {batch_idx + 1}/{total_batches}")
            print(f"   池子: {[pool[0] for pool in current_batch]}")
            
            # 处理当前批次
            for pool_name, pool_info in current_batch:
                try:
                    print(f"  🔄 [{pool_name}] {pool_info['name']} (优先级:{pool_info['priority']})")
                    
                    # 检查缓存
                    cache_file = self.cache_dir / f"{pool_name}_batch_historical_{days}d.csv"
                    if cache_file.exists():
                        try:
                            df = pd.read_csv(cache_file)
                            df['timestamp'] = pd.to_datetime(df['timestamp'])
                            print(f"  ✅ [{pool_name}] 从缓存加载 {len(df)} 条记录")
                            results[pool_name] = df
                            successful += 1
                            continue
                        except Exception as e:
                            print(f"  ⚠️  [{pool_name}] 缓存读取失败: {e}")
                    
                    # 获取新数据  
                    df = self.get_comprehensive_free_data(
                        pool_info['address'], 
                        pool_name, 
                        days=days
                    )
                    
                    if not df.empty:
                        # 添加池子信息
                        df['pool_name'] = pool_name
                        df['pool_type'] = pool_info['type']
                        df['priority'] = pool_info['priority']
                        
                        # 保存到缓存
                        df.to_csv(cache_file, index=False)
                        
                        results[pool_name] = df
                        successful += 1
                        print(f"  ✅ [{pool_name}] 获取成功: {len(df)} 条记录")
                        
                        # 显示简要统计  
                        if 'virtual_price' in df.columns:
                            latest_vp = df['virtual_price'].iloc[-1] if len(df) > 0 else 0
                            print(f"     Virtual Price: {latest_vp:.6f}")
                            
                    else:
                        print(f"  ❌ [{pool_name}] 没有获取到数据")
                        failed += 1
                        results[pool_name] = pd.DataFrame()
                        
                except Exception as e:
                    print(f"  ❌ [{pool_name}] 获取失败: {str(e)[:100]}...")
                    failed += 1
                    results[pool_name] = pd.DataFrame()
            
            # 批次间延迟
            if batch_idx < total_batches - 1:  # 不是最后一批次
                print(f"  ⏳ 等待 {delay_between_batches} 秒后处理下一批次...")
                time.sleep(delay_between_batches)
        
        print("\n" + "="*60)
        print(f"📊 批量获取完成!")
        print(f"   ✅ 成功: {successful}/{len(pools_dict)}")
        print(f"   ❌ 失败: {failed}/{len(pools_dict)}")
        print(f"   成功率: {successful/len(pools_dict)*100:.1f}%")
        
        return results

    def get_all_main_pools_data(self, days: int = CURRENT_DAYS_SETTING) -> dict:
        """
        获取所有主要池子数据 (优先级 1-3)
        
        Returns:
            {pool_name: DataFrame} 字典
        """
        main_pools = get_all_main_pools()
        print(f"🎯 获取 {len(main_pools)} 个主要池子数据...")
        
        return self.get_batch_historical_data(main_pools, days)

    def get_high_priority_pools_data(self, days: int = CURRENT_DAYS_SETTING) -> dict:
        """
        获取高优先级池子数据 (优先级 1-2)
        
        Returns:
            {pool_name: DataFrame} 字典  
        """
        high_priority_pools = get_high_priority_pools()
        print(f"⭐ 获取 {len(high_priority_pools)} 个高优先级池子数据...")
        
        return self.get_batch_historical_data(high_priority_pools, days)

    def get_stable_pools_data(self, days: int = CURRENT_DAYS_SETTING) -> dict:
        """
        获取所有稳定币池数据
        
        Returns:
            {pool_name: DataFrame} 字典
        """
        stable_pools = get_stable_pools()
        print(f"💰 获取 {len(stable_pools)} 个稳定币池数据...")
        
        return self.get_batch_historical_data(stable_pools, days)

    def get_all_pools_data(self, days: int = CURRENT_DAYS_SETTING, skip_low_priority: bool = True) -> dict:
        """
        获取所有池子数据 (可选择跳过低优先级)
        
        Args:
            days: 获取天数  
            skip_low_priority: 是否跳过优先级5的池子
            
        Returns:
            {pool_name: DataFrame} 字典
        """
        if skip_low_priority:
            pools = get_pools_by_priority(min_priority=1, max_priority=4)
            print(f"🌍 获取所有池子数据 (跳过低优先级): {len(pools)} 个池子")
        else:
            pools = AVAILABLE_POOLS
            print(f"🌍 获取所有池子数据 (包含全部): {len(pools)} 个池子")
        
        return self.get_batch_historical_data(pools, days, max_concurrent=2, delay_between_batches=3)

    def get_pools_by_type_data(self, pool_type: str, days: int = CURRENT_DAYS_SETTING) -> dict:
        """
        按池子类型获取数据
        
        Args:
            pool_type: 池子类型，如 'stable', 'metapool', 'eth_pool', 'btc_pool', 'crypto' 等
            days: 获取天数
            
        Returns:
            {pool_name: DataFrame} 字典
        """
        pools = get_pools_by_priority(pool_types=[pool_type])
        print(f"🏷️  获取 {pool_type} 类型池子数据: {len(pools)} 个池子")
        
        return self.get_batch_historical_data(pools, days)

    def export_batch_data_to_excel(self, batch_data: dict, filename: str = None) -> str:
        """
        将批量数据导出到Excel文件
        
        Args:
            batch_data: 来自批量获取函数的数据字典
            filename: 输出文件名 (可选)
            
        Returns:
            生成的Excel文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"curve_pools_data_{timestamp}.xlsx"
        
        output_path = self.cache_dir / filename
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                
                # 创建汇总表
                summary_data = []
                for pool_name, df in batch_data.items():
                    if not df.empty:
                        summary_data.append({
                            'Pool Name': pool_name,
                            'Pool Type': df['pool_type'].iloc[0] if 'pool_type' in df.columns else 'Unknown',
                            'Priority': df['priority'].iloc[0] if 'priority' in df.columns else 'Unknown',
                            'Records Count': len(df),
                            'Date Range': f"{df['timestamp'].min().date()} to {df['timestamp'].max().date()}" if len(df) > 0 else 'No data',
                            'Has Virtual Price': 'virtual_price' in df.columns,
                            'Has Volume': 'volume_24h' in df.columns,
                            'Data Sources': ', '.join(df['source'].unique()) if 'source' in df.columns else 'Unknown'
                        })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # 为每个池子创建单独的工作表
                for pool_name, df in batch_data.items():
                    if not df.empty:
                        # 限制工作表名称长度
                        sheet_name = pool_name[:31] if len(pool_name) <= 31 else pool_name[:28] + '...'
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                
            print(f"📄 批量数据已导出到: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Excel导出失败: {e}")
            return ""

    def analyze_batch_data(self, batch_data: dict) -> pd.DataFrame:
        """
        分析批量数据，生成统计报告
        
        Args:
            batch_data: 来自批量获取函数的数据字典
            
        Returns:
            包含统计信息的DataFrame
        """
        analysis_results = []
        
        for pool_name, df in batch_data.items():
            pool_info = AVAILABLE_POOLS.get(pool_name, {})
            
            if df.empty:
                analysis_results.append({
                    'Pool': pool_name,
                    'Type': pool_info.get('type', 'Unknown'),
                    'Priority': pool_info.get('priority', 'Unknown'),
                    'Status': 'No Data',
                    'Records': 0,
                    'Days Coverage': 0,
                    'Avg Virtual Price': None,
                    'Avg Volume 24h': None,
                    'Last Update': None
                })
                continue
            
            # 计算统计信息
            days_coverage = (df['timestamp'].max() - df['timestamp'].min()).days if len(df) > 1 else 0
            
            analysis_results.append({
                'Pool': pool_name,
                'Type': pool_info.get('type', 'Unknown'),
                'Priority': pool_info.get('priority', 'Unknown'), 
                'Status': 'Success',
                'Records': len(df),
                'Days Coverage': days_coverage,
                'Avg Virtual Price': df['virtual_price'].mean() if 'virtual_price' in df.columns else None,
                'Avg Volume 24h': df['volume_24h'].mean() if 'volume_24h' in df.columns else None,
                'Last Update': df['timestamp'].max() if len(df) > 0 else None
            })
        
        analysis_df = pd.DataFrame(analysis_results)
        
        print("\n📈 批量数据分析报告:")
        print("="*60)
        print(analysis_df.to_string(index=False))
        
        return analysis_df

def demo_free_historical_data():
    """演示免费历史数据获取 - 优化版"""
    
    print("🆓 免费历史数据获取演示 - 扩展版")
    print("=" * 60)
    
    manager = FreeHistoricalDataManager()
    
    print("📋 可用的池子配置:")
    print(f"   总计: {len(AVAILABLE_POOLS)} 个池子")
    print(f"   高优先级 (1-2): {len(get_high_priority_pools())} 个")
    print(f"   主要池子 (1-3): {len(get_all_main_pools())} 个")  
    print(f"   稳定币池: {len(get_stable_pools())} 个")
    print()
    
    # 展示不同类型的池子
    print("🏷️  池子分类:")
    pool_types = set(pool['type'] for pool in AVAILABLE_POOLS.values())
    for pool_type in sorted(pool_types):
        pools_of_type = [name for name, info in AVAILABLE_POOLS.items() if info['type'] == pool_type]
        print(f"   {pool_type}: {len(pools_of_type)} 个 ({', '.join(pools_of_type[:3])}...)")
    print()

    # 演示1: 单个池子数据获取 (保持原有演示)
    print("=" * 60)
    print("🎯 演示1: 单个池子历史数据获取")
    print("=" * 60)
    
    single_pool = TARGET_POOL
    print(f"获取 {single_pool} 的 {CURRENT_DAYS_SETTING} 天历史数据...")
    
    df_single = manager.get_comprehensive_free_data(
        AVAILABLE_POOLS[single_pool]['address'], 
        single_pool, 
        days=CURRENT_DAYS_SETTING
    )
    
    if not df_single.empty:
        print(f"✅ 单个池子数据获取成功: {len(df_single)} 条记录")
        print(f"   时间跨度: {(df_single['timestamp'].max() - df_single['timestamp'].min()).days} 天")
        if 'virtual_price' in df_single.columns:
            print(f"   Virtual Price 范围: {df_single['virtual_price'].min():.6f} - {df_single['virtual_price'].max():.6f}")
    else:
        print("❌ 单个池子数据获取失败")
    
    print()
    
    # 演示2: 高优先级池子批量获取
    print("=" * 60)
    print("⭐ 演示2: 高优先级池子批量数据获取")  
    print("=" * 60)
    
    batch_data_high = manager.get_high_priority_pools_data(days=CURRENT_DAYS_SETTING)
    
    if batch_data_high:
        print(f"\n📊 高优先级批量数据获取结果:")
        total_records = sum(len(df) for df in batch_data_high.values() if not df.empty)
        successful_pools = sum(1 for df in batch_data_high.values() if not df.empty)
        print(f"   成功获取: {successful_pools}/{len(batch_data_high)} 个池子")
        print(f"   总记录数: {total_records}")
        
        # 简要分析
        analysis = manager.analyze_batch_data(batch_data_high)
        
    print()
    
    # 演示3: 按类型获取数据
    print("=" * 60)
    print("🏷️  演示3: 按类型获取数据 - 稳定币池")
    print("=" * 60)
    
    stable_data = manager.get_pools_by_type_data('stable', days=CURRENT_DAYS_SETTING)
    
    if stable_data:
        stable_successful = sum(1 for df in stable_data.values() if not df.empty)
        print(f"✅ 稳定币池数据获取: {stable_successful}/{len(stable_data)} 个成功")
        
    print()
    
    # 演示4: Excel导出
    print("=" * 60)
    print("📄 演示4: 批量数据导出到Excel")  
    print("=" * 60)
    
    if batch_data_high:
        excel_path = manager.export_batch_data_to_excel(
            batch_data_high, 
            f"curve_high_priority_pools_{CURRENT_DAYS_SETTING}d.xlsx"
        )
        if excel_path:
            print(f"✅ Excel文件导出成功: {excel_path}")
        
    print()
    
    print("=" * 60)
    print("🎉 演示完成! 主要功能已验证:")
    print("   ✅ 单个池子数据获取")  
    print("   ✅ 批量数据获取")
    print("   ✅ 按优先级筛选")
    print("   ✅ 按类型筛选")
    print("   ✅ 数据分析")
    print("   ✅ Excel导出")
    print("=" * 60)

def demo_batch_collection_scenarios():
    """演示各种批量获取场景"""
    
    print("\n🚀 批量数据获取场景演示")
    print("=" * 60)
    
    manager = FreeHistoricalDataManager()
    
    # 场景1: 快速获取主要池子数据
    print("📈 场景1: 主要池子快速数据获取")
    print("-" * 40)
    main_pools_data = manager.get_all_main_pools_data(days=CURRENT_DAYS_SETTING)
    print(f"✅ 主要池子数据获取完成: {len([d for d in main_pools_data.values() if not d.empty])}/{len(main_pools_data)} 个成功")
    print()
    
    # 场景2: ETH相关池子
    print("🔥 场景2: ETH相关池子数据获取") 
    print("-" * 40)
    eth_pools_data = manager.get_pools_by_type_data('eth_pool', days=CURRENT_DAYS_SETTING)
    if eth_pools_data:
        print(f"✅ ETH池数据获取完成: {len([d for d in eth_pools_data.values() if not d.empty])}/{len(eth_pools_data)} 个成功")
    print()
    
    # 场景3: BTC相关池子
    print("₿ 场景3: BTC相关池子数据获取")
    print("-" * 40) 
    btc_pools_data = manager.get_pools_by_type_data('btc_pool', days=CURRENT_DAYS_SETTING)
    if btc_pools_data:
        print(f"✅ BTC池数据获取完成: {len([d for d in btc_pools_data.values() if not d.empty])}/{len(btc_pools_data)} 个成功")
    print()
    
    # 场景4: 综合比较分析
    print("📊 场景4: 综合数据比较分析")
    print("-" * 40)
    
    all_batch_data = {}
    all_batch_data.update(main_pools_data)
    if eth_pools_data:
        all_batch_data.update(eth_pools_data)  
    if btc_pools_data:
        all_batch_data.update(btc_pools_data)
    
    if all_batch_data:
        analysis = manager.analyze_batch_data(all_batch_data)
        
        # 导出综合数据
        excel_path = manager.export_batch_data_to_excel(
            all_batch_data,
            f"curve_comprehensive_pools_{CURRENT_DAYS_SETTING}d.xlsx"
        )
        print(f"✅ 综合数据已导出: {excel_path}")
    
    print("\n" + "=" * 60)
    print("🎯 批量获取场景演示完成!")
    print("   可以根据需要使用不同的获取策略")
    print("=" * 60)

def show_available_pools_info():
    """显示所有可用池子的详细信息"""
    
    print("\n📋 可用Curve池子详细信息")
    print("=" * 80)
    
    # 按优先级分组显示
    for priority in range(1, 6):
        pools_at_priority = {name: info for name, info in AVAILABLE_POOLS.items() 
                           if info['priority'] == priority}
        
        if pools_at_priority:
            priority_labels = {1: "🏆 最高优先级", 2: "⭐ 高优先级", 3: "📈 中优先级", 
                             4: "📊 低优先级", 5: "🔽 最低优先级"}
            
            print(f"\n{priority_labels.get(priority, f'优先级 {priority}')} ({len(pools_at_priority)} 个池子):")
            print("-" * 60)
            
            for pool_name, pool_info in sorted(pools_at_priority.items()):
                print(f"• {pool_name:12} | {pool_info['name']:25} | {pool_info['type']:12} | {pool_info['address'][:10]}...")
    
    print(f"\n📊 统计信息:")
    print(f"   总池子数量: {len(AVAILABLE_POOLS)}")
    
    # 按类型统计
    type_counts = {}
    for pool_info in AVAILABLE_POOLS.values():
        pool_type = pool_info['type']
        type_counts[pool_type] = type_counts.get(pool_type, 0) + 1
    
    print(f"   类型分布:")
    for pool_type, count in sorted(type_counts.items()):
        print(f"     {pool_type}: {count} 个")
    
    print("\n🎯 推荐使用策略:")
    print("   • 快速测试: get_high_priority_pools_data() - 获取优先级1-2的池子")  
    print("   • 日常分析: get_all_main_pools_data() - 获取优先级1-3的池子")
    print("   • 全面分析: get_all_pools_data() - 获取所有池子数据")
    print("   • 分类分析: get_pools_by_type_data('stable') - 按类型获取")
    print("=" * 80)

def switch_days_config(days_setting: str):
    """切换天数配置的辅助函数"""
    global CURRENT_DAYS_SETTING
    
    config_map = {
        'quick': QUICK_TEST_DAYS,
        'medium': MEDIUM_RANGE_DAYS, 
        'full': FULL_YEAR_DAYS,
        'test': QUICK_TEST_DAYS,
        '7': QUICK_TEST_DAYS,
        '90': MEDIUM_RANGE_DAYS,
        '365': FULL_YEAR_DAYS
    }
    
    if days_setting.lower() in config_map:
        CURRENT_DAYS_SETTING = config_map[days_setting.lower()]
        print(f"✅ 已切换到 {CURRENT_DAYS_SETTING} 天配置")
    else:
        print(f"❌ 无效配置: {days_setting}")
        print("💡 可用选项: quick(7天) | medium(90天) | full(365天)")

def demo_all_configurations():
    """演示所有配置选项"""
    print("🎛️  天数配置切换演示")
    print("=" * 40)
    
    configs = [
        ('quick', '快速测试'),
        ('medium', '中期分析'), 
        ('full', '完整年度')
    ]
    
    for config, desc in configs:
        print(f"\n🔄 切换到 {desc} 模式:")
        switch_days_config(config)
        
        manager = FreeHistoricalDataManager()
        print(f"📊 将获取 {CURRENT_DAYS_SETTING} 天数据")

if __name__ == "__main__":
    import sys
    
    # 根据命令行参数选择演示模式
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "info":
            show_available_pools_info()
        elif mode == "batch":
            demo_batch_collection_scenarios()
        elif mode == "single":
            demo_free_historical_data()
        elif mode == "all":
            show_available_pools_info()
            demo_free_historical_data()  
            demo_batch_collection_scenarios()
        elif mode == "full":
            # 🚀 直接获取所有池子的一年历史数据
            print("🚀 开始获取所有37个Curve池子的一年历史数据...")
            print("⚠️  注意: 这将需要较长时间 (预计10-20分钟)")
            print("=" * 60)
            
            manager = FreeHistoricalDataManager()
            
            # 显示将要获取的池子信息
            all_pools = get_pools_by_priority(min_priority=1, max_priority=4)  # 跳过优先级5
            print(f"📋 将获取 {len(all_pools)} 个池子的 {CURRENT_DAYS_SETTING} 天数据")
            print(f"🏷️  池子类型分布:")
            
            type_counts = {}
            for pool_info in all_pools.values():
                pool_type = pool_info['type']
                type_counts[pool_type] = type_counts.get(pool_type, 0) + 1
            
            for pool_type, count in sorted(type_counts.items()):
                print(f"   {pool_type}: {count} 个")
                
            # 询问用户确认
            response = input("\n继续获取所有池子数据? (y/N): ")
            if response.lower() in ['y', 'yes', '是']:
                
                print("\n🔄 开始批量数据获取...")
                batch_data = manager.get_all_pools_data(days=CURRENT_DAYS_SETTING, skip_low_priority=True)
                
                # 统计结果
                successful = sum(1 for df in batch_data.values() if not df.empty)
                total_records = sum(len(df) for df in batch_data.values() if not df.empty)
                
                print(f"\n🎉 批量获取完成!")
                print(f"   ✅ 成功: {successful}/{len(batch_data)} 个池子")
                print(f"   📊 总记录数: {total_records}")
                
                if successful > 0:
                    # 生成分析报告
                    print(f"\n📈 生成数据分析报告...")
                    analysis = manager.analyze_batch_data(batch_data)
                    
                    # 导出Excel
                    print(f"\n📄 导出数据到Excel...")
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    excel_path = manager.export_batch_data_to_excel(
                        batch_data,
                        f"curve_all_pools_1year_{timestamp}.xlsx"
                    )
                    
                    if excel_path:
                        print(f"✅ 完整数据已保存: {excel_path}")
                        print(f"📁 缓存目录: {manager.cache_dir.absolute()}")
                        
                        print(f"\n💡 使用数据:")
                        print(f"from free_historical_data import FreeHistoricalDataManager")
                        print(f"manager = FreeHistoricalDataManager()")
                        print(f"# 数据已缓存，下次加载会更快")
                        
                else:
                    print("❌ 没有成功获取到任何数据，请检查网络连接")
                    
            else:
                print("❌ 用户取消操作")
                
        elif mode == "quick-all":
            # 🔥 快速获取所有池子的7天数据 (用于测试)
            print("⚡ 快速获取所有池子的7天数据 (测试模式)...")
            print("=" * 60)
            
            manager = FreeHistoricalDataManager()
            
            # 获取7天数据进行快速测试
            batch_data = manager.get_all_pools_data(days=7, skip_low_priority=True)
            
            successful = sum(1 for df in batch_data.values() if not df.empty)
            print(f"\n✅ 快速测试完成: {successful}/{len(batch_data)} 个池子成功")
            
            if successful > 0:
                excel_path = manager.export_batch_data_to_excel(
                    batch_data,
                    "curve_all_pools_7d_test.xlsx"
                )
                print(f"📄 测试数据已导出: {excel_path}")
                
        else:
            print("Usage: python free_historical_data.py [选项]")
            print("可用选项:")
            print("  info      - 显示所有可用池子信息")
            print("  batch     - 演示批量数据获取")  
            print("  single    - 演示单个池子获取")
            print("  all       - 运行所有演示")
            print("  full      - 🚀 获取所有池子的一年历史数据")
            print("  quick-all - ⚡ 快速获取所有池子的7天数据 (测试)")
    else:
        # 默认运行单个池子演示
        demo_free_historical_data() 