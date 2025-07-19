#!/usr/bin/env python3
"""
扩展Curve池子支持示例
展示如何添加新的池子到系统中
"""

import requests
from typing import Dict, List, Optional
from real_data_collector import CurveRealDataCollector

class CurvePoolExpander:
    """Curve池子扩展器"""
    
    def __init__(self):
        self.curve_api_base = "https://api.curve.fi"
        
    def discover_popular_pools(self, min_tvl_usd: float = 10_000_000) -> List[Dict]:
        """自动发现热门池子 (TVL > 1000万)"""
        
        print(f"🔍 自动发现TVL超过${min_tvl_usd:,.0f}的热门池子...")
        
        try:
            # 获取所有以太坊池子
            response = requests.get(f"{self.curve_api_base}/api/getPools/ethereum/main", timeout=15)
            
            if response.status_code != 200:
                print(f"❌ API请求失败: {response.status_code}")
                return []
            
            pools_data = response.json()['data']['poolData']
            
            # 筛选高TVL池子
            popular_pools = []
            
            for pool in pools_data:
                tvl = float(pool.get('usdTotal', 0))
                
                if tvl >= min_tvl_usd:
                    pool_info = {
                        'name': pool['name'],
                        'address': pool['address'],
                        'tvl_usd': tvl,
                        'tokens': [coin['symbol'] for coin in pool['coins']],
                        'decimals': [int(coin['decimals']) for coin in pool['coins']],
                        'volume_24h': float(pool.get('volumeUSD', 0)),
                        'apy': float(pool.get('latestDailyApy', 0)) / 100
                    }
                    popular_pools.append(pool_info)
            
            # 按TVL排序
            popular_pools.sort(key=lambda x: x['tvl_usd'], reverse=True)
            
            print(f"✅ 发现 {len(popular_pools)} 个热门池子")
            return popular_pools
            
        except Exception as e:
            print(f"❌ 发现池子失败: {e}")
            return []
    
    def generate_pool_config(self, pools: List[Dict]) -> str:
        """生成池子配置代码"""
        
        print("📝 生成池子配置代码...")
        
        config_code = "# 扩展的Curve池子配置\nEXTENDED_CURVE_POOLS = {\n"
        
        for pool in pools:
            # 生成池子key (简化名称)
            pool_key = pool['name'].lower().replace(' ', '_').replace('-', '_')
            
            config_code += f"    '{pool_key}': {{\n"
            config_code += f"        'address': '{pool['address']}',\n"
            config_code += f"        'name': '{pool['name']}',\n"
            config_code += f"        'tokens': {pool['tokens']},\n"
            config_code += f"        'decimals': {pool['decimals']},\n"
            config_code += f"        'tvl_usd': {pool['tvl_usd']:,.0f},\n"
            config_code += f"        'volume_24h': {pool['volume_24h']:,.0f},\n"
            config_code += f"        'apy': {pool['apy']:.4f},\n"
            config_code += f"        'description': '{'/'.join(pool['tokens'])} pool'\n"
            config_code += "    },\n"
        
        config_code += "}\n"
        
        return config_code
    
    def test_pool_data_quality(self, pool_address: str, pool_name: str) -> Dict:
        """测试新池子的数据质量"""
        
        print(f"🧪 测试 {pool_name} 数据质量...")
        
        collector = CurveRealDataCollector()
        quality_report = {
            'pool_name': pool_name,
            'pool_address': pool_address,
            'api_data_available': False,
            'subgraph_data_available': False,
            'data_completeness': 0,
            'issues': []
        }
        
        # 测试API数据
        try:
            api_data = collector.get_curve_api_data(pool_name)
            if api_data:
                quality_report['api_data_available'] = True
                quality_report['data_completeness'] += 50
            else:
                quality_report['issues'].append('API数据不可用')
        except Exception as e:
            quality_report['issues'].append(f'API测试失败: {e}')
        
        # 测试子图数据
        try:
            subgraph_data = collector.query_subgraph(pool_address, days=1)
            if subgraph_data is not None and not subgraph_data.empty:
                quality_report['subgraph_data_available'] = True
                quality_report['data_completeness'] += 50
            else:
                quality_report['issues'].append('子图数据不可用')
        except Exception as e:
            quality_report['issues'].append(f'子图测试失败: {e}')
        
        # 评估数据质量
        if quality_report['data_completeness'] >= 80:
            quality_report['recommendation'] = '推荐添加'
        elif quality_report['data_completeness'] >= 50:
            quality_report['recommendation'] = '可以添加，但数据有限'
        else:
            quality_report['recommendation'] = '不推荐添加'
        
        return quality_report

def demo_pool_expansion():
    """演示池子扩展功能"""
    
    print("🚀 Curve池子扩展演示")
    print("=" * 60)
    
    expander = CurvePoolExpander()
    
    # 1. 发现热门池子
    print("1️⃣ 发现热门池子 (TVL > 2000万)")
    popular_pools = expander.discover_popular_pools(min_tvl_usd=20_000_000)
    
    if popular_pools:
        print(f"\n📊 发现的热门池子 (前10个):")
        print("排名 | 池子名称 | TVL | 代币组合 | 24h交易量")
        print("-" * 60)
        
        for i, pool in enumerate(popular_pools[:10], 1):
            tvl_str = f"${pool['tvl_usd']:,.0f}"
            volume_str = f"${pool['volume_24h']:,.0f}"
            tokens_str = "/".join(pool['tokens'])
            print(f"{i:2d}   | {pool['name']:<15} | {tvl_str:>10} | {tokens_str:<12} | {volume_str:>10}")
    
    # 2. 生成配置代码
    if popular_pools:
        print(f"\n2️⃣ 生成前5个池子的配置代码:")
        config_code = expander.generate_pool_config(popular_pools[:5])
        
        # 保存到文件
        with open('extended_pools_config.py', 'w', encoding='utf-8') as f:
            f.write(config_code)
        
        print("✅ 配置代码已保存到: extended_pools_config.py")
        print("\n配置代码预览:")
        print("-" * 40)
        print(config_code[:500] + "..." if len(config_code) > 500 else config_code)
    
    # 3. 测试数据质量
    if popular_pools:
        print(f"\n3️⃣ 测试前3个池子的数据质量:")
        
        for pool in popular_pools[:3]:
            print(f"\n🧪 测试 {pool['name']}...")
            quality_report = expander.test_pool_data_quality(
                pool['address'], 
                pool['name'].lower().replace(' ', '_')
            )
            
            print(f"   📊 数据完整性: {quality_report['data_completeness']}%")
            print(f"   🔍 API数据: {'✅' if quality_report['api_data_available'] else '❌'}")
            print(f"   📈 子图数据: {'✅' if quality_report['subgraph_data_available'] else '❌'}")
            print(f"   💡 建议: {quality_report['recommendation']}")
            
            if quality_report['issues']:
                print(f"   ⚠️  问题: {'; '.join(quality_report['issues'])}")
    
    print(f"\n" + "=" * 60)
    print("💡 如何使用扩展的池子:")
    print("1. 将 extended_pools_config.py 中的配置复制到 config.py")
    print("2. 在 real_data_collector.py 中添加新的池子地址映射")
    print("3. 重新运行数据收集和训练脚本")
    print("4. 享受更多池子的数据分析！")

# 多链扩展示例
def demo_multichain_expansion():
    """演示多链扩展可能性"""
    
    print("\n🌐 多链扩展演示")
    print("=" * 40)
    
    # 可用的链和对应API端点
    supported_chains = {
        'ethereum': 'https://api.curve.fi/api/getPools/ethereum/main',
        'polygon': 'https://api.curve.fi/api/getPools/polygon/main', 
        'arbitrum': 'https://api.curve.fi/api/getPools/arbitrum/main',
        'optimism': 'https://api.curve.fi/api/getPools/optimism/main',
        'avalanche': 'https://api.curve.fi/api/getPools/avalanche/main',
        'fantom': 'https://api.curve.fi/api/getPools/fantom/main'
    }
    
    print("📋 可扩展的链:")
    for chain, endpoint in supported_chains.items():
        print(f"  - {chain.title()}: {endpoint}")
    
    print(f"\n💡 扩展方法:")
    print("1. 修改 real_data_collector.py 添加链选择参数")
    print("2. 为每个链创建独立的池子配置")  
    print("3. 更新API调用逻辑支持多链端点")
    print("4. 适配不同链的代币精度和命名")

if __name__ == "__main__":
    demo_pool_expansion()
    demo_multichain_expansion() 