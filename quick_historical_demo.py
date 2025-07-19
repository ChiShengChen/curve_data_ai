#!/usr/bin/env python3
"""
快速历史数据获取 (只用The Graph API，几分钟完成)
"""
from free_historical_data import FreeHistoricalDataManager

def quick_demo():
    print("🚀 快速获取30天历史数据 (仅使用The Graph)")
    
    manager = FreeHistoricalDataManager()
    
    # 只使用The Graph API，几分钟内完成
    df = manager.get_thegraph_historical_data(
        "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7", 
        days=30
    )
    
    if not df.empty:
        print(f"✅ 快速完成！获取 {len(df)} 条记录")
        
        # 保存数据
        filepath = manager.cache_dir / "quick_30d_historical.csv"
        df.to_csv(filepath, index=False)
        print(f"📁 已保存到: {filepath}")
    else:
        print("❌ 获取失败")

if __name__ == "__main__":
    quick_demo()
