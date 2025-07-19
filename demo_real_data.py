#!/usr/bin/env python3
"""
Curve真实数据获取演示脚本
展示如何从各种数据源获取真实的Curve协议数据
"""

import asyncio
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

from config import Config
from real_data_collector import CurveRealDataCollector

def demo_config_status():
    """演示配置状态检查"""
    print("🔧 配置状态检查")
    print("=" * 50)
    
    Config.print_config_status()
    
    validation = Config.validate_config()
    
    if not validation['has_web3_provider']:
        print("⚠️  建议设置Web3 API密钥以获取更准确的数据")
        print("   你可以从以下网站免费获取API密钥：")
        print("   - Infura: https://infura.io/register")
        print("   - Alchemy: https://alchemy.com/")
        
    print("\n" + "=" * 50)

def demo_real_time_data():
    """演示实时数据获取"""
    print("📊 实时数据获取演示")
    print("=" * 50)
    
    # 使用配置中的Web3提供商
    web3_url = Config.get_web3_provider_url()
    collector = CurveRealDataCollector(web3_url)
    
    # 测试不同池子的数据获取
    pools_to_test = ['3pool', 'frax']
    
    for pool_name in pools_to_test:
        print(f"\n🏊 获取 {pool_name} 池子数据...")
        
        try:
            pool_data = collector.get_real_time_data(pool_name)
            
            if pool_data:
                print(f"✅ 成功获取 {pool_data.pool_name} 数据:")
                print(f"   地址: {pool_data.pool_address}")
                print(f"   代币: {' / '.join(pool_data.tokens)}")
                print(f"   余额: {[f'{b:,.0f}' for b in pool_data.balances]}")
                print(f"   Virtual Price: {pool_data.virtual_price:.6f}")
                print(f"   24小时交易量: ${pool_data.volume_24h:,.0f}")
                print(f"   APY: {pool_data.apy:.2%}")
                print(f"   更新时间: {pool_data.timestamp}")
                
                # 计算池子不平衡度
                total_balance = sum(pool_data.balances)
                if len(pool_data.tokens) == 3:  # 3Pool
                    ideal_balance = total_balance / 3
                    imbalances = [(b - ideal_balance) / ideal_balance * 100 
                                 for b in pool_data.balances]
                    print(f"   不平衡度: {[f'{i:+.2f}%' for i in imbalances]}")
            else:
                print(f"❌ 无法获取 {pool_name} 数据")
                
        except Exception as e:
            print(f"❌ 获取 {pool_name} 数据时出错: {e}")
        
        time.sleep(1)  # 避免API限流

def demo_historical_data():
    """演示历史数据获取和分析"""
    print("\n📈 历史数据获取演示")
    print("=" * 50)
    
    web3_url = Config.get_web3_provider_url()
    collector = CurveRealDataCollector(web3_url)
    
    print("获取3Pool过去7天的历史数据...")
    
    try:
        df = collector.get_historical_data('3pool', days=7)
        
        if not df.empty:
            print(f"✅ 获取到 {len(df)} 条历史记录")
            print(f"时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
            
            # 基本统计信息
            if 'usdc_balance' in df.columns:
                print("\n📊 余额统计 (最近7天):")
                balance_cols = [col for col in df.columns if 'balance' in col]
                for col in balance_cols:
                    token = col.replace('_balance', '').upper()
                    print(f"   {token}: {df[col].mean():,.0f} (avg), "
                          f"{df[col].std():,.0f} (std)")
            
            if 'volume_24h' in df.columns:
                print(f"\n💹 交易量统计:")
                print(f"   平均日交易量: ${df['volume_24h'].mean():,.0f}")
                print(f"   最高日交易量: ${df['volume_24h'].max():,.0f}")
                print(f"   最低日交易量: ${df['volume_24h'].min():,.0f}")
            
            # 绘制图表
            if len(df) > 1:
                plot_historical_data(df)
            
        else:
            print("❌ 未获取到历史数据")
            
    except Exception as e:
        print(f"❌ 获取历史数据时出错: {e}")

def plot_historical_data(df: pd.DataFrame):
    """绘制历史数据图表"""
    try:
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Curve 3Pool 历史数据分析', fontsize=16)
        
        # 1. 余额变化
        balance_cols = [col for col in df.columns if 'balance' in col]
        if balance_cols and 'timestamp' in df.columns:
            ax1 = axes[0, 0]
            for col in balance_cols[:3]:  # 最多显示3个
                token = col.replace('_balance', '').upper()
                ax1.plot(df['timestamp'], df[col], label=token, alpha=0.8)
            ax1.set_title('代币余额变化')
            ax1.set_ylabel('余额')
            ax1.legend()
            ax1.tick_params(axis='x', rotation=45)
        
        # 2. Virtual Price
        if 'virtual_price' in df.columns:
            ax2 = axes[0, 1]
            ax2.plot(df['timestamp'], df['virtual_price'], color='green', alpha=0.8)
            ax2.set_title('Virtual Price')
            ax2.set_ylabel('Price')
            ax2.tick_params(axis='x', rotation=45)
        
        # 3. 交易量
        if 'volume_24h' in df.columns:
            ax3 = axes[1, 0]
            ax3.bar(df['timestamp'], df['volume_24h'], alpha=0.7, color='blue')
            ax3.set_title('24小时交易量')
            ax3.set_ylabel('交易量 ($)')
            ax3.tick_params(axis='x', rotation=45)
        
        # 4. TVL
        if 'tvl' in df.columns:
            ax4 = axes[1, 1]
            ax4.plot(df['timestamp'], df['tvl'], color='orange', alpha=0.8)
            ax4.set_title('总锁定价值 (TVL)')
            ax4.set_ylabel('TVL ($)')
            ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('curve_historical_data.png', dpi=300, bbox_inches='tight')
        print("\n📊 历史数据图表已保存到: curve_historical_data.png")
        
        # 不显示图片，只保存
        plt.close()
        
    except Exception as e:
        print(f"⚠️  绘制图表时出错: {e}")

def demo_data_quality():
    """演示数据质量检查"""
    print("\n🔍 数据质量检查演示")
    print("=" * 50)
    
    web3_url = Config.get_web3_provider_url()
    collector = CurveRealDataCollector(web3_url)
    
    print("检查3Pool数据质量...")
    
    try:
        # 获取实时数据
        pool_data = collector.get_real_time_data('3pool')
        
        if pool_data:
            print("✅ 数据可用性检查:")
            
            # 基本数据检查
            checks = {
                '池子地址': bool(pool_data.pool_address),
                '代币列表': len(pool_data.tokens) > 0,
                '余额数据': len(pool_data.balances) > 0 and all(b > 0 for b in pool_data.balances),
                'Virtual Price': pool_data.virtual_price > 0,
                '交易量数据': pool_data.volume_24h >= 0,
                'APY数据': 0 <= pool_data.apy <= 1,
                '时间戳': pool_data.timestamp is not None
            }
            
            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check_name}")
            
            # 数据合理性检查
            print("\n🧐 数据合理性检查:")
            
            # 稳定币价格检查 (应该接近1美元)
            total_balance = sum(pool_data.balances)
            if len(pool_data.tokens) == 3:
                balance_ratios = [b / total_balance for b in pool_data.balances]
                max_deviation = max(abs(r - 1/3) for r in balance_ratios)
                
                if max_deviation < 0.1:  # 10%以内偏离
                    print("   ✅ 池子平衡度正常 (偏离 < 10%)")
                else:
                    print(f"   ⚠️  池子存在不平衡 (最大偏离: {max_deviation:.1%})")
            
            # APY合理性
            if 0 < pool_data.apy < 0.5:  # 0-50% APY
                print(f"   ✅ APY合理: {pool_data.apy:.2%}")
            elif pool_data.apy == 0:
                print("   ⚠️  APY数据缺失")
            else:
                print(f"   ❓ APY异常: {pool_data.apy:.2%}")
                
        else:
            print("❌ 无法获取数据进行质量检查")
            
    except Exception as e:
        print(f"❌ 数据质量检查时出错: {e}")

def demo_multi_source_comparison():
    """演示多数据源对比"""
    print("\n🔄 多数据源对比演示")
    print("=" * 50)
    
    web3_url = Config.get_web3_provider_url()
    collector = CurveRealDataCollector(web3_url)
    
    print("对比不同数据源的3Pool数据...")
    
    # 比较不同API的数据
    sources_data = {}
    
    try:
        # Curve API
        print("📡 尝试Curve API...")
        curve_data = collector.get_curve_api_data('3pool')
        if curve_data:
            sources_data['Curve API'] = curve_data
            print("✅ Curve API数据获取成功")
        else:
            print("❌ Curve API数据获取失败")
        
        # 如果有多个数据源，进行对比
        if len(sources_data) > 1:
            print("\n📊 数据源对比:")
            
            for source, data in sources_data.items():
                print(f"\n{source}:")
                print(f"  Virtual Price: {data.virtual_price:.6f}")
                print(f"  Volume 24h: ${data.volume_24h:,.0f}")
                print(f"  APY: {data.apy:.2%}")
        
        elif len(sources_data) == 1:
            print(f"\n✅ 成功从 {list(sources_data.keys())[0]} 获取数据")
        else:
            print("\n❌ 所有数据源都无法获取数据")
    
    except Exception as e:
        print(f"❌ 多数据源对比时出错: {e}")

def main():
    """主演示函数"""
    print("🌐 Curve真实数据获取完整演示")
    print("=" * 60)
    print(f"开始时间: {datetime.now()}")
    print()
    
    # 1. 配置状态检查
    demo_config_status()
    
    # 2. 实时数据获取
    demo_real_time_data()
    
    # 3. 历史数据获取
    demo_historical_data()
    
    # 4. 数据质量检查
    demo_data_quality()
    
    # 5. 多数据源对比
    demo_multi_source_comparison()
    
    print("\n" + "=" * 60)
    print("🎉 演示完成!")
    print("📁 生成的文件:")
    print("   - curve_historical_data.png (历史数据图表)")
    print()
    print("💡 下一步建议:")
    print("1. 设置API密钥以获取更准确的数据")
    print("2. 运行 python config.py 查看配置状态")
    print("3. 使用真实数据训练模型: python train_curve_model.py --use-real-data")

if __name__ == "__main__":
    main() 