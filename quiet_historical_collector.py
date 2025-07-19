#!/usr/bin/env python3
"""
安静版本的历史数据收集器
减少重复日志输出，只显示进度
"""

from free_historical_data import FreeHistoricalDataManager
from real_data_collector import CurveRealDataCollector
import pandas as pd
from datetime import datetime, timedelta

class QuietHistoricalCollector:
    """安静的历史数据收集器"""
    
    def __init__(self):
        self.manager = FreeHistoricalDataManager()
        self.collector = CurveRealDataCollector()
    
    def collect_with_progress(self, pool_name: str = '3pool', days: int = 30):
        """带进度显示的数据收集，减少重复日志"""
        
        print(f"🏗️  开始收集 {pool_name} 的 {days} 天历史数据...")
        print(f"📊 预计收集 {days * 24} 个数据点")
        
        records = []
        total_hours = days * 24
        
        for hour in range(total_hours):
            try:
                # 临时关闭详细日志
                import sys
                from contextlib import redirect_stdout
                import io
                
                # 捕获输出但不显示
                with redirect_stdout(io.StringIO()):
                    pool_data = self.collector.get_real_time_data(pool_name)
                
                if pool_data:
                    record = {
                        'timestamp': datetime.now() - timedelta(hours=total_hours - hour),
                        'pool_name': pool_data.pool_name,
                        'virtual_price': pool_data.virtual_price,
                        'volume_24h': pool_data.volume_24h,
                        'apy': pool_data.apy,
                    }
                    
                    # 添加代币余额
                    for i, (token, balance) in enumerate(zip(pool_data.tokens, pool_data.balances)):
                        record[f'{token.lower()}_balance'] = balance
                    
                    records.append(record)
                
                # 每10%显示一次进度
                if hour % (total_hours // 10) == 0:
                    progress = (hour / total_hours) * 100
                    print(f"📈 进度: {progress:.0f}% ({hour}/{total_hours})")
                    
            except Exception as e:
                if hour % (total_hours // 10) == 0:  # 只在进度点显示错误
                    print(f"⚠️  第{hour}小时收集失败: {e}")
        
        if records:
            df = pd.DataFrame(records)
            filename = f"{pool_name}_quiet_historical_{days}d.csv"
            filepath = self.manager.cache_dir / filename
            df.to_csv(filepath, index=False)
            
            print(f"✅ 收集完成!")
            print(f"📁 保存位置: {filepath}")
            print(f"📊 成功收集: {len(df)} 条记录")
            return df
        
        return pd.DataFrame()

def demo_quiet_collection():
    """演示安静的数据收集"""
    print("🔇 安静模式历史数据收集")
    print("=" * 40)
    
    collector = QuietHistoricalCollector()
    
    # 收集7天数据作为演示 (比30天快)
    df = collector.collect_with_progress(pool_name='3pool', days=7)
    
    if not df.empty:
        print(f"\n📊 数据概览:")
        print(f"  时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        print(f"  记录数量: {len(df)}")
        print(f"  数据列数: {len(df.columns)}")

if __name__ == "__main__":
    demo_quiet_collection() 