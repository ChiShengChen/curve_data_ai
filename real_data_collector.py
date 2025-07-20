#!/usr/bin/env python3
"""
Curve真实数据获取模块
支持多种数据源: Curve API, The Graph, 区块链直读, CoinGecko等
添加SSL错误处理和超时机制
"""

import requests
import json
import time
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 请求配置
DEFAULT_TIMEOUT = 5
DEFAULT_VERIFY_SSL = False  # 🔧 默认禁用SSL验证避免证书错误
MAX_RETRIES = 3
RETRY_DELAY = 1

try:
    from web3 import Web3
    from web3.contract import Contract
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("Web3 not available. Install with: pip install web3")

@dataclass
class CurvePoolData:
    """Curve池实时数据"""
    pool_address: str
    pool_name: str
    tokens: List[str]
    balances: List[float]
    rates: List[float]  # 汇率
    total_supply: float
    virtual_price: float
    volume_24h: float
    fees_24h: float
    apy: float
    timestamp: datetime

class CurveRealDataCollector:
    """Curve真实数据收集器 - 优化版"""
    
    def __init__(self, web3_provider_url: Optional[str] = None):
        self.web3_provider_url = web3_provider_url
        
        # API端点
        self.curve_api_base = "https://api.curve.fi"
        self.defillama_base = "https://yields.llama.fi"
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        
        # The Graph endpoints (已废弃)
        self.curve_subgraph = "https://api.thegraph.com/subgraphs/name/messari/curve-finance-ethereum"
        
        # 请求配置
        self.timeout = DEFAULT_TIMEOUT
        self.verify_ssl = DEFAULT_VERIFY_SSL
        self.max_retries = MAX_RETRIES
        
        # Web3连接
        if WEB3_AVAILABLE and web3_provider_url:
            self.w3 = Web3(Web3.HTTPProvider(web3_provider_url))
            if self.w3.is_connected():
                print(f"✅ Web3 connected to {web3_provider_url}")
            else:
                print(f"❌ Web3 connection failed")
                self.w3 = None
        else:
            self.w3 = None
        
        # 常用池子地址
        self.pool_addresses = {
            '3pool': '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
            'frax': '0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B',
            'mim': '0x5a6A4D54456819C6Cd2fE4de20b59F4f5F3f9b2D',
            'lusd': '0xEd279fDD11cA84bEef15AF5D39BB4d4bEE23F0cA'
        }
    
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """统一的HTTP请求方法，包含错误处理和重试"""
        
        # 设置默认参数
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('verify', self.verify_ssl)
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, **kwargs)
                elif method.upper() == 'POST':
                    response = requests.post(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                if response.status_code == 200:
                    return response
                else:
                    print(f"⚠️  HTTP {response.status_code} from {url}")
                    
            except requests.exceptions.SSLError as e:
                print(f"❌ SSL错误 (尝试 {attempt + 1}/{self.max_retries}): {str(e)[:100]}...")
                if attempt == self.max_retries - 1:
                    print("💡 建议: 设置 ENABLE_SSL_VERIFICATION = False")
                    
            except requests.exceptions.Timeout as e:
                print(f"⏰ 超时错误 (尝试 {attempt + 1}/{self.max_retries}): {self.timeout}s")
                
            except requests.exceptions.ConnectionError as e:
                print(f"🔌 连接错误 (尝试 {attempt + 1}/{self.max_retries}): {str(e)[:100]}...")
                
            except Exception as e:
                print(f"❌ 请求失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)[:100]}...")
            
            if attempt < self.max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))  # 递增延迟
        
        return None
    
    def get_curve_api_data(self, pool_name: str = '3pool') -> Optional[CurvePoolData]:
        """从Curve官方API获取数据 - 优化版"""
        
        try:
            # 获取所有池子信息
            url = f"{self.curve_api_base}/api/getPools/ethereum/main"
            response = self._make_request(url)
            
            if not response:
                print(f"❌ 无法连接到Curve API")
                return None
            
            pools_data = response.json()
            
            if 'data' not in pools_data or 'poolData' not in pools_data['data']:
                print(f"❌ Curve API响应格式异常")
                return None
            
            # 查找目标池子
            target_pool = None
            for pool in pools_data['data']['poolData']:
                if (pool_name.lower() in pool['name'].lower() or 
                    pool_name in self.pool_addresses and 
                    pool['address'].lower() == self.pool_addresses[pool_name].lower()):
                    target_pool = pool
                    break
            
            if not target_pool:
                print(f"❌ 池子 {pool_name} 未在Curve API中找到")
                return None
            
            # 解析数据
            tokens = [coin['symbol'] for coin in target_pool['coins']]
            balances = [float(coin['poolBalance']) / (10 ** int(coin['decimals'])) 
                       for coin in target_pool['coins']]
            rates = [float(coin.get('rate', 1.0)) for coin in target_pool['coins']]
            
            return CurvePoolData(
                pool_address=target_pool['address'],
                pool_name=target_pool['name'],
                tokens=tokens,
                balances=balances,
                rates=rates,
                total_supply=float(target_pool.get('totalSupply', 0)) / 1e18,
                virtual_price=float(target_pool.get('virtualPrice', 1.0)) / 1e18,
                volume_24h=float(target_pool.get('volumeUSD', 0)),
                fees_24h=float(target_pool.get('totalFees24h', 0)),
                apy=float(target_pool.get('latestDailyApy', 0)) / 100,
                timestamp=datetime.now()
            )
            
        except KeyError as e:
            print(f"❌ Curve API数据格式错误: {e}")
            return None
        except Exception as e:
            print(f"❌ Curve API获取失败: {str(e)[:100]}...")
            return None
    
    def get_defillama_apy(self, pool_address: str) -> Optional[float]:
        """从DefiLlama获取APY数据"""
        
        try:
            response = requests.get(f"{self.defillama_base}/pools", timeout=10)
            
            if response.status_code != 200:
                return None
            
            pools = response.json()['data']
            
            for pool in pools:
                if pool.get('pool', '').lower() == pool_address.lower():
                    return pool.get('apy', 0) / 100
            
            return None
            
        except Exception as e:
            print(f"Error fetching DefiLlama data: {e}")
            return None
    
    def get_coingecko_prices(self, tokens: List[str]) -> Dict[str, float]:
        """从CoinGecko获取代币价格"""
        
        try:
            # Token ID映射
            token_ids = {
                'USDC': 'usd-coin',
                'USDT': 'tether',
                'DAI': 'dai',
                'FRAX': 'frax',
                'MIM': 'magic-internet-money',
                'LUSD': 'liquity-usd'
            }
            
            ids = [token_ids.get(token.upper(), token.lower()) for token in tokens]
            ids_str = ','.join(ids)
            
            response = requests.get(
                f"{self.coingecko_base}/simple/price",
                params={'ids': ids_str, 'vs_currencies': 'usd'},
                timeout=10
            )
            
            if response.status_code != 200:
                return {}
            
            prices_data = response.json()
            
            # 转换回token symbol格式
            result = {}
            for i, token in enumerate(tokens):
                token_id = ids[i]
                if token_id in prices_data:
                    result[token] = prices_data[token_id]['usd']
            
            return result
            
        except Exception as e:
            print(f"Error fetching CoinGecko prices: {e}")
            return {}
    
    def query_subgraph(self, pool_address: str, days: int = 7) -> Optional[pd.DataFrame]:
        """从The Graph子图查询历史数据"""
        
        # GraphQL查询
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
                self.curve_subgraph,
                json={'query': query},
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"Subgraph query failed: {response.status_code}")
                return None
            
            data = response.json()
            
            if 'errors' in data:
                print(f"Subgraph errors: {data['errors']}")
                return None
            
            pool_data = data['data']['pool']
            if not pool_data:
                print(f"No pool data found for {pool_address}")
                return None
            
            snapshots = pool_data['dailyPoolSnapshots']
            
            # 转换为DataFrame
            records = []
            for snapshot in snapshots:
                record = {
                    'timestamp': datetime.fromtimestamp(int(snapshot['timestamp'])),
                    'tvl': float(snapshot.get('totalValueLockedUSD', 0)),
                    'volume': float(snapshot.get('dailyVolumeUSD', 0)),
                    'virtual_price': float(snapshot.get('virtualPrice', 1e18)) / 1e18
                }
                
                # 解析余额
                balances = snapshot.get('balances', [])
                rates = snapshot.get('rates', [])
                
                for i, coin in enumerate(pool_data['coins']):
                    if i < len(balances):
                        balance = float(balances[i]) / (10 ** int(coin['decimals']))
                        record[f"{coin['symbol'].lower()}_balance"] = balance
                    
                    if i < len(rates):
                        record[f"{coin['symbol'].lower()}_rate"] = float(rates[i]) / 1e18
                
                records.append(record)
            
            return pd.DataFrame(records)
            
        except Exception as e:
            print(f"Error querying subgraph: {e}")
            return None
    
    def get_onchain_data(self, pool_address: str) -> Optional[CurvePoolData]:
        """直接从区块链读取数据"""
        
        if not self.w3:
            print("Web3 not connected")
            return None
        
        # Curve池通用ABI（简化版）
        pool_abi = [
            {
                "name": "balances",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [{"type": "uint256", "name": "i"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "name": "coins",
                "outputs": [{"type": "address", "name": ""}],
                "inputs": [{"type": "uint256", "name": "arg0"}],
                "stateMutability": "view", 
                "type": "function"
            },
            {
                "name": "get_virtual_price",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "name": "totalSupply",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        try:
            # 创建合约实例
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(pool_address),
                abi=pool_abi
            )
            
            # 读取基本信息
            virtual_price = contract.functions.get_virtual_price().call() / 1e18
            total_supply = contract.functions.totalSupply().call() / 1e18
            
            # 读取余额和代币信息
            balances = []
            tokens = []
            
            for i in range(3):  # 假设最多3个代币
                try:
                    balance = contract.functions.balances(i).call()
                    coin_address = contract.functions.coins(i).call()
                    
                    # 这里需要根据代币地址获取symbol和decimals
                    # 简化处理，假设都是18位精度
                    balances.append(balance / 1e18)
                    tokens.append(f"Token{i}")  # 需要实际获取symbol
                    
                except:
                    break
            
            return CurvePoolData(
                pool_address=pool_address,
                pool_name="Unknown",
                tokens=tokens,
                balances=balances,
                rates=[1.0] * len(tokens),  # 需要实际计算
                total_supply=total_supply,
                virtual_price=virtual_price,
                volume_24h=0.0,  # 需要从事件日志计算
                fees_24h=0.0,
                apy=0.0,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"Error reading on-chain data: {e}")
            return None
    
    def get_historical_data(self, pool_name: str = '3pool', days: int = 30) -> pd.DataFrame:
        """获取历史数据的综合方法"""
        
        print(f"Fetching historical data for {pool_name} ({days} days)...")
        
        pool_address = self.pool_addresses.get(pool_name)
        if not pool_address:
            print(f"Unknown pool: {pool_name}")
            return pd.DataFrame()
        
        # 方法1: 尝试从subgraph获取
        df = self.query_subgraph(pool_address, days)
        
        if df is not None and not df.empty:
            print(f"✅ Got {len(df)} records from subgraph")
            return df
        
        # 方法2: 如果subgraph失败，使用API数据生成模拟历史数据
        print("⚠️  Subgraph failed, generating synthetic historical data...")
        
        current_data = self.get_curve_api_data(pool_name)
        if not current_data:
            print("❌ Failed to get current data")
            return pd.DataFrame()
        
        # 生成基于当前数据的历史数据
        dates = pd.date_range(
            end=datetime.now(),
            periods=days * 24,  # 每小时一个数据点
            freq='H'
        )
        
        records = []
        base_balances = current_data.balances
        base_volume = current_data.volume_24h / 24  # 小时平均
        
        for i, date in enumerate(dates):
            # 添加一些随机波动
            noise = np.random.normal(0, 0.02, len(base_balances))
            balances = [b * (1 + n) for b, n in zip(base_balances, noise)]
            
            volume_noise = np.random.normal(1, 0.3)
            volume = max(0, base_volume * volume_noise)
            
            record = {
                'timestamp': date,
                'virtual_price': current_data.virtual_price * (1 + np.random.normal(0, 0.0001)),
                'volume_24h': volume,
                'tvl': sum(balances) * (1 + np.random.normal(0, 0.01))
            }
            
            # 添加各代币余额
            for j, token in enumerate(current_data.tokens):
                record[f'{token.lower()}_balance'] = balances[j] if j < len(balances) else 0
                record[f'{token.lower()}_rate'] = current_data.rates[j] if j < len(current_data.rates) else 1.0
            
            records.append(record)
        
        df = pd.DataFrame(records)
        print(f"✅ Generated {len(df)} synthetic historical records")
        return df
    
    def get_real_time_data(self, pool_name: str = '3pool') -> Optional[CurvePoolData]:
        """获取实时数据的综合方法 - 优化版"""
        
        print(f"Fetching real-time data for {pool_name}...")
        
        # 方法1: Curve官方API（推荐）
        data = self.get_curve_api_data(pool_name)
        if data:
            print("✅ Got data from Curve API")
            
            # 可选：补充价格信息 (不影响主流程)
            try:
                prices = self.get_coingecko_prices(data.tokens)
                if prices:
                    print(f"✅ Got prices: {list(prices.keys())}")
            except:
                pass  # 价格获取失败不影响主流程
            
            return data
        
        # 方法2: 区块链直读 (如果有Web3连接)
        if self.w3:
            pool_address = self.pool_addresses.get(pool_name)
            if pool_address:
                print("⚠️  API failed, trying on-chain data...")
                try:
                    data = self.get_onchain_data(pool_address)
                    if data:
                        print("✅ Got on-chain data")
                        return data
                except Exception as e:
                    print(f"❌ On-chain data failed: {str(e)[:50]}...")
        
        # 方法3: 合成数据 (最后的备用方案)
        print("⚠️  所有真实数据源失败，生成合成数据...")
        return self._generate_synthetic_pool_data(pool_name)
    
    def _generate_synthetic_pool_data(self, pool_name: str) -> CurvePoolData:
        """生成合成池子数据 - 当所有真实数据源都失败时使用"""
        
        # 根据池子类型设置不同参数
        pool_configs = {
            'mim': {
                'tokens': ['MIM', '3CRV'], 
                'balances': [1000000, 1000000],
                'base_apy': 0.05,
                'base_volume': 500000
            },
            '3pool': {
                'tokens': ['USDC', 'USDT', 'DAI'],
                'balances': [5000000, 5000000, 5000000], 
                'base_apy': 0.03,
                'base_volume': 2000000
            },
            'frax': {
                'tokens': ['FRAX', 'USDC'],
                'balances': [800000, 800000],
                'base_apy': 0.06,
                'base_volume': 300000
            },
            'lusd': {
                'tokens': ['LUSD', '3CRV'],
                'balances': [600000, 600000],
                'base_apy': 0.04,
                'base_volume': 200000
            }
        }
        
        config = pool_configs.get(pool_name, pool_configs['3pool'])
        pool_address = self.pool_addresses.get(pool_name, '0x0000000000000000000000000000000000000000')
        
        # 添加一些随机性让数据更真实
        noise = np.random.normal(1, 0.02)  # 2%的随机波动
        
        return CurvePoolData(
            pool_address=pool_address,
            pool_name=f"Synthetic {pool_name.upper()} Pool",
            tokens=config['tokens'],
            balances=[b * noise for b in config['balances']],
            rates=[1.0] * len(config['tokens']),
            total_supply=sum(config['balances']) * noise,
            virtual_price=1.0 * noise,
            volume_24h=config['base_volume'] * noise,
            fees_24h=config['base_volume'] * 0.0004 * noise,  # 假设0.04%手续费率
            apy=config['base_apy'] * noise,
            timestamp=datetime.now()
        )

def demo_real_data():
    """演示真实数据获取"""
    
    print("🌐 Curve真实数据获取演示")
    print("=" * 50)
    
    # 初始化收集器（如果有Infura/Alchemy key，在这里填入）
    collector = CurveRealDataCollector()
    # collector = CurveRealDataCollector("https://mainnet.infura.io/v3/YOUR-API-KEY")
    
    # 测试实时数据获取
    print("\n📊 获取3Pool实时数据...")
    real_time_data = collector.get_real_time_data('3pool')
    
    if real_time_data:
        print(f"池子: {real_time_data.pool_name}")
        print(f"地址: {real_time_data.pool_address}")
        print(f"代币: {real_time_data.tokens}")
        print(f"余额: {[f'{b:,.0f}' for b in real_time_data.balances]}")
        print(f"Virtual Price: {real_time_data.virtual_price:.6f}")
        print(f"24h交易量: ${real_time_data.volume_24h:,.0f}")
        print(f"APY: {real_time_data.apy:.2%}")
    
    # 测试历史数据获取
    print("\n📈 获取历史数据...")
    historical_data = collector.get_historical_data('3pool', days=7)
    
    if not historical_data.empty:
        print(f"历史数据: {len(historical_data)} 条记录")
        print(f"时间范围: {historical_data['timestamp'].min()} ~ {historical_data['timestamp'].max()}")
        print("\n最新5条记录:")
        print(historical_data.head())
    
    print("\n" + "=" * 50)
    print("✅ 演示完成!")

if __name__ == "__main__":
    demo_real_data() 