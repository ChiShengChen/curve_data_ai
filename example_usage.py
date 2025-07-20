#!/usr/bin/env python3
"""
🚀 Curve池子批量数据获取 - 完整使用示例
展示如何使用新的扩展功能获取所有主要Curve池子的数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from free_historical_data import (
    FreeHistoricalDataManager,
    get_high_priority_pools, 
    get_all_main_pools,
    get_stable_pools,
    get_pools_by_priority,
    AVAILABLE_POOLS
)
import pandas as pd
from datetime import datetime

def example_1_high_priority_quick_start():
    """示例1: 快速开始 - 获取高优先级池子数据"""
    
    print("\n📈 示例1: 快速开始 - 高优先级池子")
    print("=" * 50)
    
    # 创建管理器
    manager = FreeHistoricalDataManager()
    
    # 获取高优先级池子数据 (优先级1-2)
    print("获取高优先级池子数据...")
    batch_data = manager.get_high_priority_pools_data(days=7)
    
    # 显示结果
    successful = sum(1 for df in batch_data.values() if not df.empty)
    print(f"✅ 成功获取 {successful}/{len(batch_data)} 个池子数据")
    
    # 显示每个池子的基本信息
    for pool_name, df in batch_data.items():
        if not df.empty:
            latest_vp = df['virtual_price'].iloc[-1] if 'virtual_price' in df.columns else 'N/A'
            print(f"  • {pool_name:12}: {len(df):3} 条记录, Virtual Price: {latest_vp}")
    
    return batch_data

def example_2_by_pool_type():
    """示例2: 按池子类型获取数据"""
    
    print("\n🏷️  示例2: 按池子类型获取数据") 
    print("=" * 50)
    
    manager = FreeHistoricalDataManager()
    
    # 获取不同类型的池子数据
    pool_types = ['stable', 'eth_pool', 'btc_pool', 'metapool']
    
    results = {}
    for pool_type in pool_types:
        print(f"\n📊 获取 {pool_type} 类型池子数据...")
        try:
            type_data = manager.get_pools_by_type_data(pool_type, days=7)
            successful = sum(1 for df in type_data.values() if not df.empty)
            print(f"  ✅ 成功: {successful}/{len(type_data)} 个池子")
            results[pool_type] = type_data
        except Exception as e:
            print(f"  ❌ 失败: {e}")
    
    return results

def example_3_comprehensive_analysis():
    """示例3: 综合分析 - 获取主要池子并进行分析"""
    
    print("\n📈 示例3: 综合分析")
    print("=" * 50)
    
    manager = FreeHistoricalDataManager()
    
    # 获取所有主要池子数据 (优先级1-3)
    print("获取所有主要池子数据...")
    main_data = manager.get_all_main_pools_data(days=7)
    
    # 进行数据分析
    print("\n分析数据...")
    analysis = manager.analyze_batch_data(main_data)
    
    # 导出到Excel
    print("\n导出数据到Excel...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
    excel_path = manager.export_batch_data_to_excel(
        main_data,
        f"curve_main_pools_analysis_{timestamp}.xlsx"
    )
    
    if excel_path:
        print(f"✅ Excel文件已生成: {excel_path}")
    
    return main_data, analysis

def example_4_custom_selection():
    """示例4: 自定义选择 - 按优先级和类型筛选"""
    
    print("\n🎯 示例4: 自定义池子选择")
    print("=" * 50)
    
    manager = FreeHistoricalDataManager()
    
    # 示例A: 获取优先级1-3的稳定币池
    print("A. 获取高优先级稳定币池 (优先级1-3)...")
    stable_pools = get_pools_by_priority(
        min_priority=1,
        max_priority=3, 
        pool_types=['stable', 'metapool']
    )
    
    stable_data = manager.get_batch_historical_data(stable_pools, days=7)
    successful_stable = sum(1 for df in stable_data.values() if not df.empty)
    print(f"   ✅ 稳定币池: {successful_stable}/{len(stable_data)} 个成功")
    
    # 示例B: 获取所有ETH相关池子
    print("\nB. 获取所有ETH相关池子...")
    eth_pools = get_pools_by_priority(pool_types=['eth_pool'])
    eth_data = manager.get_batch_historical_data(eth_pools, days=7)
    successful_eth = sum(1 for df in eth_data.values() if not df.empty)
    print(f"   ✅ ETH池: {successful_eth}/{len(eth_data)} 个成功")
    
    # 示例C: 获取所有BTC相关池子
    print("\nC. 获取所有BTC相关池子...")
    btc_pools = get_pools_by_priority(pool_types=['btc_pool', 'btc_metapool'])
    btc_data = manager.get_batch_historical_data(btc_pools, days=7)
    successful_btc = sum(1 for df in btc_data.values() if not df.empty)
    print(f"   ✅ BTC池: {successful_btc}/{len(btc_data)} 个成功")
    
    return {
        'stable': stable_data,
        'eth': eth_data, 
        'btc': btc_data
    }

def example_5_data_processing():
    """示例5: 数据处理和分析"""
    
    print("\n🔬 示例5: 数据处理和分析")
    print("=" * 50)
    
    manager = FreeHistoricalDataManager()
    
    # 获取一些数据
    high_priority_data = manager.get_high_priority_pools_data(days=7)
    
    print("数据处理示例:")
    
    for pool_name, df in high_priority_data.items():
        if df.empty:
            continue
            
        print(f"\n📊 {pool_name} 池子分析:")
        print(f"   数据点数: {len(df)}")
        
        if 'virtual_price' in df.columns:
            vp_min = df['virtual_price'].min()
            vp_max = df['virtual_price'].max() 
            vp_mean = df['virtual_price'].mean()
            print(f"   Virtual Price: {vp_min:.6f} - {vp_max:.6f} (平均: {vp_mean:.6f})")
            
        if 'volume_24h' in df.columns and df['volume_24h'].sum() > 0:
            volume_mean = df['volume_24h'].mean()
            volume_max = df['volume_24h'].max()
            print(f"   24h交易量: 平均 ${volume_mean:,.0f}, 最高 ${volume_max:,.0f}")
            
        if 'timestamp' in df.columns and len(df) > 1:
            time_span = (df['timestamp'].max() - df['timestamp'].min()).days
            print(f"   时间跨度: {time_span} 天")
    
    return high_priority_data

def example_6_production_ready():
    """示例6: 生产环境就绪的完整流程"""
    
    print("\n🏭 示例6: 生产环境完整流程")
    print("=" * 50)
    
    try:
        manager = FreeHistoricalDataManager()
        
        # 第1步: 获取所有重要池子的数据
        print("📥 第1步: 批量获取数据...")
        all_important_pools = get_pools_by_priority(min_priority=1, max_priority=3)
        batch_data = manager.get_batch_historical_data(
            all_important_pools, 
            days=7,
            max_concurrent=2,  # 限制并发避免API限制
            delay_between_batches=3  # 增加延迟避免封禁
        )
        
        # 第2步: 数据质量检查
        print("\n🔍 第2步: 数据质量检查...")
        successful_pools = []
        failed_pools = []
        
        for pool_name, df in batch_data.items():
            if not df.empty and len(df) >= 5:  # 至少要有5个数据点
                successful_pools.append(pool_name)
            else:
                failed_pools.append(pool_name)
        
        print(f"   ✅ 合格: {len(successful_pools)} 个池子")
        print(f"   ❌ 不合格: {len(failed_pools)} 个池子")
        
        if failed_pools:
            print(f"   不合格池子: {', '.join(failed_pools)}")
        
        # 第3步: 生成分析报告
        print("\n📊 第3步: 生成分析报告...")
        analysis = manager.analyze_batch_data(batch_data)
        
        # 第4步: 导出结果
        print("\n📄 第4步: 导出结果...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 导出到Excel
        excel_path = manager.export_batch_data_to_excel(
            batch_data,
            f"curve_production_data_{timestamp}.xlsx"
        )
        
        # 保存分析报告
        if not analysis.empty:
            csv_path = f"free_historical_cache/curve_analysis_report_{timestamp}.csv"
            analysis.to_csv(csv_path, index=False)
            print(f"✅ 分析报告: {csv_path}")
        
        print(f"\n🎉 生产流程完成!")
        print(f"   数据获取: {len(successful_pools)}/{len(all_important_pools)} 成功")
        print(f"   Excel导出: {excel_path}")
        
        return batch_data, analysis
        
    except Exception as e:
        print(f"❌ 生产流程失败: {e}")
        return None, None

def main():
    """主函数 - 运行所有示例"""
    
    print("🚀 Curve池子批量数据获取 - 完整使用示例")
    print("=" * 60)
    print(f"📋 当前支持 {len(AVAILABLE_POOLS)} 个主要Curve池子")
    print("=" * 60)
    
    # 运行所有示例
    examples = [
        ("快速开始", example_1_high_priority_quick_start),
        ("按类型获取", example_2_by_pool_type),  
        ("综合分析", example_3_comprehensive_analysis),
        ("自定义选择", example_4_custom_selection),
        ("数据处理", example_5_data_processing),
        ("生产流程", example_6_production_ready)
    ]
    
    results = {}
    
    for name, example_func in examples:
        print(f"\n{'='*60}")
        print(f"🔄 运行示例: {name}")
        print(f"{'='*60}")
        
        try:
            result = example_func()
            results[name] = result
            print(f"✅ 示例 '{name}' 完成")
        except Exception as e:
            print(f"❌ 示例 '{name}' 失败: {e}")
            results[name] = None
    
    # 总结
    print(f"\n{'='*60}")
    print("🎉 所有示例运行完成!")
    print(f"{'='*60}")
    
    successful_examples = sum(1 for result in results.values() if result is not None)
    print(f"成功完成: {successful_examples}/{len(examples)} 个示例")
    
    print(f"\n💡 现在你已经掌握了如何:")
    print("   • 获取高优先级池子数据")
    print("   • 按池子类型筛选数据") 
    print("   • 进行批量数据分析")
    print("   • 自定义池子选择策略")
    print("   • 处理和分析池子数据")
    print("   • 建立生产环境数据流程")
    
    print(f"\n🚀 开始你的Curve数据分析之旅吧!")
    return results

if __name__ == "__main__":
    # 可以通过命令行参数选择运行特定示例
    if len(sys.argv) > 1:
        example_name = sys.argv[1].lower()
        
        if example_name == "1" or example_name == "quick":
            example_1_high_priority_quick_start()
        elif example_name == "2" or example_name == "type":
            example_2_by_pool_type()
        elif example_name == "3" or example_name == "analysis":
            example_3_comprehensive_analysis()
        elif example_name == "4" or example_name == "custom":
            example_4_custom_selection()
        elif example_name == "5" or example_name == "process":
            example_5_data_processing()
        elif example_name == "6" or example_name == "production":
            example_6_production_ready()
        else:
            print("可用示例:")
            print("  python example_usage.py 1     # 快速开始")
            print("  python example_usage.py 2     # 按类型获取")
            print("  python example_usage.py 3     # 综合分析") 
            print("  python example_usage.py 4     # 自定义选择")
            print("  python example_usage.py 5     # 数据处理")
            print("  python example_usage.py 6     # 生产流程")
    else:
        # 默认运行所有示例
        main() 