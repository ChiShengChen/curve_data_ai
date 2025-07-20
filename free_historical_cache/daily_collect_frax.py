#!/usr/bin/env python3
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
        filename = 'daily_collection_frax.csv'
        filepath = manager.cache_dir / filename
        
        if filepath.exists():
            existing_df = pd.read_csv(filepath)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            combined_df = df
        
        combined_df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"✅ {datetime.now()}: 每日数据收集完成，共{len(combined_df)}条记录")
    else:
        print(f"❌ {datetime.now()}: 今日数据收集失败")

if __name__ == "__main__":
    daily_collect()
