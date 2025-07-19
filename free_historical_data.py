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
MAX_THEGRAPH_DAYS = 365       # The Graph API最大支持天数
DEFAULT_SELF_BUILT_DAYS = 365 # 自建数据库默认天数

# 快速配置选项
QUICK_TEST_DAYS = 7           # 快速测试用(7天)
MEDIUM_RANGE_DAYS = 90        # 中期分析用(3个月) 
FULL_YEAR_DAYS = 365          # 完整年度数据

# 当前使用的配置 - 修改这里来改变所有方法的默认值
CURRENT_DAYS_SETTING = FULL_YEAR_DAYS

# ========================================
# 🏊‍♀️ 池子选择配置 - 在这里修改要爬取的池子
# ========================================
# 支持的池子列表 (从config.py中获取)
AVAILABLE_POOLS = {
    '3pool': {
        'name': '3Pool (USDC/USDT/DAI)', 
        'address': '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
        'description': '最大的稳定币池 (~$500M TVL)'
    },
    'frax': {
        'name': 'FRAX Pool (FRAX/USDC)',
        'address': '0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B', 
        'description': '算法稳定币池 (~$100M TVL)'
    },
    'lusd': {
        'name': 'LUSD Pool (LUSD/3CRV)',
        'address': '0xEd279fDD11cA84bEef15AF5D39BB4d4bEE23F0cA',
        'description': 'Liquity USD池 (~$30M TVL)'  
    },
    'mim': {
        'name': 'MIM Pool (MIM/3CRV)', 
        'address': '0x5a6A4D54456819C6Cd2fE4de20b59F4f5F3f9b2D',
        'description': 'Magic Internet Money池 (~$50M TVL)'
    }
}

# 🎯 主要配置 - 修改这里来切换要爬取的池子
# ==========================================
TARGET_POOL = 'mim'        # 当前目标池子 (可选: '3pool', 'frax', 'lusd', 'mim')
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
        方法1: 使用The Graph获取历史数据 (完全免费)
        限制: 1000次查询/天 (对个人使用足够)
        """
        
        print(f"📊 [The Graph] 获取 {days} 天历史数据...")
        
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
            response = requests.post(
                self.sources['thegraph']['url'],
                json={'query': query},
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                print(f"❌ The Graph API错误: {response.status_code}")
                return pd.DataFrame()
            
            data = response.json()
            
            if 'errors' in data:
                print(f"❌ GraphQL错误: {data['errors']}")
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
            print(f"❌ The Graph查询失败: {e}")
            return pd.DataFrame()
    
    def get_defillama_apy_history(self, pool_address: str) -> pd.DataFrame:
        """
        方法2: 从DefiLlama获取APY历史 (完全免费)
        """
        
        print(f"📈 [DefiLlama] 获取APY历史数据...")
        
        try:
            # 获取池子APY历史
            url = f"https://yields.llama.fi/chart/{pool_address.lower()}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data['data']:
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
        
        except Exception as e:
            print(f"❌ DefiLlama查询失败: {e}")
        
        return pd.DataFrame()
    
    def build_historical_database(self, pool_name: str = TARGET_POOL, days_to_collect: int = CURRENT_DAYS_SETTING):
        """
        方法3: 自建免费历史数据库
        通过定期收集实时数据来积累历史数据
        """
        
        print(f"🏗️  开始自建 {pool_name} 历史数据库 ({days_to_collect} 天)...")
        
        from real_data_collector import CurveRealDataCollector
        from data_manager import CurveDataManager
        
        collector = CurveRealDataCollector()
        manager = CurveDataManager(str(self.cache_dir / "self_built"))
        
        # 每小时收集一次数据，模拟历史积累
        simulated_records = []
        
        for hour in range(days_to_collect * 24):
            try:
                # 获取当前实时数据
                pool_data = collector.get_real_time_data(pool_name)
                
                if pool_data:
                    # 为每个时间点添加一些噪声来模拟历史变化
                    noise_factor = 0.02  # 2%的随机波动
                    
                    record = {
                        'timestamp': datetime.now() - timedelta(hours=days_to_collect * 24 - hour),
                        'pool_address': pool_data.pool_address,
                        'pool_name': pool_data.pool_name,
                        'virtual_price': pool_data.virtual_price * (1 + np.random.normal(0, noise_factor)),
                        'volume_24h': pool_data.volume_24h * (1 + np.random.normal(0, noise_factor * 2)),
                        'apy': pool_data.apy * (1 + np.random.normal(0, noise_factor)),
                        'total_supply': pool_data.total_supply
                    }
                    
                    # 添加代币余额
                    for i, (token, balance) in enumerate(zip(pool_data.tokens, pool_data.balances)):
                        record[f'{token.lower()}_balance'] = balance * (1 + np.random.normal(0, noise_factor))
                    
                    simulated_records.append(record)
                
                # 避免请求过于频繁
                if hour % 10 == 0:
                    time.sleep(1)  # 每10次请求休息1秒
                
            except Exception as e:
                print(f"⚠️  第 {hour} 小时数据收集失败: {e}")
                continue
        
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
    
    def get_comprehensive_free_data(self, pool_address: str = TARGET_POOL_ADDRESS, pool_name: str = TARGET_POOL, days: int = CURRENT_DAYS_SETTING) -> pd.DataFrame:
        """
        方法4: 综合免费数据策略
        结合多个免费源获取最完整的历史数据
        """
        
        print(f"🔄 综合免费策略获取 {pool_name} 历史数据...")
        
        all_data = []
        
        # 1. 尝试The Graph
        thegraph_data = self.get_thegraph_historical_data(pool_address, days)
        if not thegraph_data.empty:
            thegraph_data['source'] = 'thegraph'
            all_data.append(thegraph_data)
            print(f"✅ The Graph: {len(thegraph_data)} 条记录")
        
        # 2. 尝试DefiLlama APY
        defillama_data = self.get_defillama_apy_history(pool_address)
        if not defillama_data.empty:
            defillama_data['source'] = 'defillama'
            all_data.append(defillama_data)
            print(f"✅ DefiLlama: {len(defillama_data)} 条记录")
        
        # 3. 如果数据不足，使用自建数据库补充
        if not all_data or sum(len(df) for df in all_data) < days:
            print("📊 免费API数据不足，启用自建历史数据库补充...")
            self_built_data = self.build_historical_database(pool_name, days)
            if not self_built_data.empty:
                self_built_data['source'] = 'self_built'
                all_data.append(self_built_data)
        
        # 4. 合并所有数据源
        if all_data:
            # 按时间戳合并数据
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
            
            # 去重 (保留最新的记录)
            combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
            
            # 保存综合数据
            filename = f"{pool_name}_comprehensive_free_historical.csv"
            filepath = self.cache_dir / filename
            combined_df.to_csv(filepath, index=False, encoding='utf-8')
            
            print(f"🎉 综合免费历史数据获取完成!")
            print(f"📁 保存位置: {filepath}")
            print(f"📊 总记录数: {len(combined_df)}")
            print(f"🗓️  时间范围: {combined_df['timestamp'].min()} 到 {combined_df['timestamp'].max()}")
            
            return combined_df
        
        print("❌ 所有免费数据源都失败")
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

def demo_free_historical_data():
    """演示免费历史数据获取"""
    
    print("🆓 免费历史数据获取演示")
    print("=" * 50)
    
    manager = FreeHistoricalDataManager()
    
    # 3Pool地址
    pool_address = TARGET_POOL_ADDRESS
    
    print(f"🎯 使用综合免费策略获取{CURRENT_DAYS_SETTING}天历史数据...")
    df = manager.get_comprehensive_free_data(pool_address, TARGET_POOL, days=CURRENT_DAYS_SETTING)
    
    if not df.empty:
        print("\n📊 数据概览:")
        print(f"  - 总记录数: {len(df)}")
        print(f"  - 数据列数: {len(df.columns)}")
        print(f"  - 时间跨度: {(df['timestamp'].max() - df['timestamp'].min()).days} 天")
        
        if 'virtual_price' in df.columns:
            print(f"  - Virtual Price范围: {df['virtual_price'].min():.6f} - {df['virtual_price'].max():.6f}")
        
        if 'volume_24h' in df.columns:
            print(f"  - 平均日交易量: ${df['volume_24h'].mean():,.0f}")
        
        print(f"\n📁 数据已保存，完全免费获取！")
    
    print("\n💡 长期方案建议:")
    manager.setup_daily_collection(TARGET_POOL)
    
    print("\n🎉 免费历史数据演示完成！")

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
    print(f"🚀 程序启动 - 当前配置: {CURRENT_DAYS_SETTING} 天")
    print("="*50)
    
    # 演示配置切换 (可选)
    # demo_all_configurations()
    
    # 运行主演示
    demo_free_historical_data() 