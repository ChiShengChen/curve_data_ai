#!/usr/bin/env python3
"""
免费历史数据快速演示
展示如何在不花钱的情况下获取Curve历史数据
"""

from free_historical_data import FreeHistoricalDataManager

def main():
    print("🆓 免费Curve历史数据快速演示")
    print("=" * 60)
    
    print("💡 本演示将使用完全免费的数据源:")
    print("   - The Graph Protocol (1000次查询/天)")
    print("   - DefiLlama (无限制)")
    print("   - 自建数据积累系统")
    print("")
    
    # 初始化免费数据管理器
    manager = FreeHistoricalDataManager()
    
    # 3Pool地址 (最大的Curve稳定币池)
    pool_address = "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"
    
    print("🎯 开始获取3Pool的30天历史数据...")
    print("   (这完全免费，可能需要1-2分钟)")
    print("")
    
    try:
        # 使用综合免费策略获取数据
        df = manager.get_comprehensive_free_data(
            pool_address=pool_address,
            pool_name='3pool', 
            days=30
        )
        
        if not df.empty:
            print("\n🎉 成功获取免费历史数据!")
            print("=" * 40)
            
            # 数据统计
            print(f"📊 数据概览:")
            print(f"   总记录数: {len(df)} 条")
            print(f"   数据字段: {len(df.columns)} 个")
            print(f"   时间跨度: {(df['timestamp'].max() - df['timestamp'].min()).days} 天")
            
            # 关键指标
            if 'virtual_price' in df.columns:
                vp_change = (df['virtual_price'].iloc[-1] / df['virtual_price'].iloc[0] - 1) * 100
                print(f"   Virtual Price变化: {vp_change:+.4f}%")
            
            if 'volume_24h' in df.columns:
                avg_volume = df['volume_24h'].mean()
                print(f"   平均日交易量: ${avg_volume:,.0f}")
                
            if 'apy' in df.columns:
                avg_apy = df['apy'].mean() * 100
                print(f"   平均APY: {avg_apy:.2f}%")
            
            print(f"\n💾 数据已保存到本地CSV文件")
            print(f"   可以用于训练机器学习模型")
            
            # 显示数据样本
            print(f"\n📋 数据样本 (最近3条记录):")
            display_cols = ['timestamp', 'virtual_price', 'volume_24h']
            available_cols = [col for col in display_cols if col in df.columns]
            
            if available_cols:
                sample_df = df[available_cols].tail(3)
                print(sample_df.to_string(index=False))
            
        else:
            print("❌ 未能获取到历史数据")
            print("可能的原因:")
            print("   - 网络连接问题")
            print("   - API暂时不可用")
            print("   - 池子地址错误")
            
    except Exception as e:
        print(f"❌ 演示过程出错: {e}")
        print("请检查网络连接后重试")
    
    print("\n" + "=" * 60)
    print("💡 后续步骤:")
    print("1. 使用获取的CSV数据训练模型:")
    print("   python train_curve_model.py --use-real-data --csv-data-dir free_historical_cache")
    print("")
    print("2. 设置定时任务持续积累数据:")
    print("   python -c \"from free_historical_data import FreeHistoricalDataManager; ")
    print("   FreeHistoricalDataManager().setup_daily_collection('3pool')\"")
    print("")
    print("3. 查看详细数据源说明:")
    print("   cat DATA_SOURCES.md")
    print("")
    print("🎉 免费获取Curve历史数据完成!")

if __name__ == "__main__":
    main() 