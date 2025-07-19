#!/usr/bin/env python3
"""
Curve数据管理模块
支持CSV存储、读取、清理和分析
"""

import os
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path

from real_data_collector import CurveRealDataCollector, CurvePoolData
from config import Config

class CurveDataManager:
    """Curve数据管理器"""
    
    def __init__(self, data_dir: str = "curve_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (self.data_dir / "real_time").mkdir(exist_ok=True)
        (self.data_dir / "historical").mkdir(exist_ok=True)
        (self.data_dir / "backups").mkdir(exist_ok=True)
        
        # 初始化数据收集器
        web3_url = Config.get_web3_provider_url()
        self.collector = CurveRealDataCollector(web3_url)
        
        print(f"📁 数据目录: {self.data_dir.absolute()}")
    
    def save_real_time_data(self, pool_name: str, save_csv: bool = True) -> Optional[str]:
        """获取并保存实时数据"""
        
        print(f"📊 获取 {pool_name} 实时数据...")
        
        try:
            # 获取实时数据
            pool_data = self.collector.get_real_time_data(pool_name)
            
            if not pool_data:
                print(f"❌ 无法获取 {pool_name} 数据")
                return None
            
            # 转换为DataFrame
            df = self._pool_data_to_df(pool_data)
            
            if save_csv:
                # 保存为CSV
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{pool_name}_realtime_{timestamp_str}.csv"
                filepath = self.data_dir / "real_time" / filename
                
                df.to_csv(filepath, index=False, encoding='utf-8')
                print(f"✅ 实时数据已保存: {filepath}")
                
                # 同时保存最新数据 (覆盖)
                latest_file = self.data_dir / "real_time" / f"{pool_name}_latest.csv"
                df.to_csv(latest_file, index=False, encoding='utf-8')
                
                return str(filepath)
            else:
                print(f"📊 数据获取成功但未保存 (save_csv=False)")
                return None
            
        except Exception as e:
            print(f"❌ 保存实时数据失败: {e}")
            return None
    
    def save_historical_data(self, pool_name: str, days: int = 30, save_csv: bool = True) -> Optional[str]:
        """获取并保存历史数据"""
        
        print(f"📈 获取 {pool_name} 历史数据 ({days}天)...")
        
        try:
            # 获取历史数据
            df = self.collector.get_historical_data(pool_name, days)
            
            if df.empty:
                print(f"❌ 无法获取 {pool_name} 历史数据")
                return None
            
            if save_csv:
                # 保存为CSV
                timestamp_str = datetime.now().strftime("%Y%m%d")
                filename = f"{pool_name}_historical_{days}d_{timestamp_str}.csv"
                filepath = self.data_dir / "historical" / filename
                
                df.to_csv(filepath, index=False, encoding='utf-8')
                print(f"✅ 历史数据已保存: {filepath} ({len(df)} 条记录)")
                
                return str(filepath)
            else:
                print(f"📈 历史数据获取成功但未保存 (save_csv=False)")
                return None
            
        except Exception as e:
            print(f"❌ 保存历史数据失败: {e}")
            return None
    
    def save_all_pools_data(self, pools: Optional[List[str]] = None, save_csv: bool = True) -> Dict[str, str]:
        """批量保存多个池子的数据"""
        
        if pools is None:
            pools = list(Config.CURVE_POOLS.keys())
        
        results = {}
        
        print(f"🔄 批量获取 {len(pools)} 个池子的数据...")
        
        for pool_name in pools:
            print(f"\n--- 处理 {pool_name} ---")
            
            # 实时数据
            realtime_file = self.save_real_time_data(pool_name, save_csv)
            if realtime_file:
                results[f"{pool_name}_realtime"] = realtime_file
            
            # 历史数据 (7天)
            historical_file = self.save_historical_data(pool_name, days=7, save_csv=save_csv)
            if historical_file:
                results[f"{pool_name}_historical"] = historical_file
        
        # 保存批量操作记录
        if save_csv and results:
            batch_record = {
                'timestamp': datetime.now().isoformat(),
                'pools_processed': pools,
                'files_created': results,
                'total_files': len(results)
            }
            
            record_file = self.data_dir / f"batch_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(batch_record, f, indent=2, ensure_ascii=False)
            
            print(f"\n📋 批量操作记录已保存: {record_file}")
        
        return results
    
    def load_csv_data(self, filepath: str) -> pd.DataFrame:
        """从CSV文件加载数据"""
        
        try:
            df = pd.read_csv(filepath)
            
            # 尝试解析时间戳列
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            print(f"✅ 已加载数据: {filepath} ({len(df)} 条记录)")
            return df
            
        except Exception as e:
            print(f"❌ 加载CSV失败: {e}")
            return pd.DataFrame()
    
    def get_latest_data(self, pool_name: str) -> Optional[pd.DataFrame]:
        """获取指定池子的最新数据"""
        
        latest_file = self.data_dir / "real_time" / f"{pool_name}_latest.csv"
        
        if latest_file.exists():
            return self.load_csv_data(str(latest_file))
        else:
            print(f"⚠️  未找到 {pool_name} 的最新数据，尝试获取...")
            self.save_real_time_data(pool_name)
            
            if latest_file.exists():
                return self.load_csv_data(str(latest_file))
        
        return None
    
    def list_saved_files(self) -> Dict[str, List[str]]:
        """列出所有保存的文件"""
        
        files = {
            'real_time': [],
            'historical': [],
            'backups': []
        }
        
        for category in files.keys():
            dir_path = self.data_dir / category
            if dir_path.exists():
                csv_files = list(dir_path.glob("*.csv"))
                files[category] = [f.name for f in csv_files]
        
        return files
    
    def cleanup_old_files(self, days_to_keep: int = 7):
        """清理旧文件"""
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for dir_name in ['real_time', 'historical', 'backups']:
            dir_path = self.data_dir / dir_name
            
            if dir_path.exists():
                for file_path in dir_path.glob("*.csv"):
                    # 跳过 latest 文件
                    if 'latest' in file_path.name:
                        continue
                    
                    # 检查文件修改时间
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
        
        print(f"🗑️  已清理 {deleted_count} 个超过 {days_to_keep} 天的旧文件")
    
    def create_summary_report(self) -> str:
        """创建数据汇总报告"""
        
        files = self.list_saved_files()
        
        report = ["📊 Curve数据存储汇总报告", "=" * 40]
        report.append(f"数据目录: {self.data_dir.absolute()}")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 文件统计
        total_files = sum(len(file_list) for file_list in files.values())
        report.append(f"📁 文件统计:")
        report.append(f"  - 实时数据: {len(files['real_time'])} 个文件")
        report.append(f"  - 历史数据: {len(files['historical'])} 个文件")  
        report.append(f"  - 备份文件: {len(files['backups'])} 个文件")
        report.append(f"  - 总计: {total_files} 个文件")
        report.append("")
        
        # 最新数据状态
        report.append("🔄 最新数据状态:")
        for pool_name in Config.CURVE_POOLS.keys():
            latest_file = self.data_dir / "real_time" / f"{pool_name}_latest.csv"
            if latest_file.exists():
                file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                age = datetime.now() - file_time
                status = "🟢 新" if age.total_seconds() < 3600 else "🟡 旧" if age.total_seconds() < 86400 else "🔴 过期"
                report.append(f"  - {pool_name}: {status} ({age})")
            else:
                report.append(f"  - {pool_name}: ❌ 无数据")
        
        report_text = "\n".join(report)
        
        # 保存报告
        report_file = self.data_dir / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"📋 汇总报告已保存: {report_file}")
        return report_text
    
    def _pool_data_to_df(self, pool_data: CurvePoolData) -> pd.DataFrame:
        """将CurvePoolData转换为DataFrame"""
        
        # 基本信息
        row = {
            'timestamp': pool_data.timestamp,
            'pool_address': pool_data.pool_address,
            'pool_name': pool_data.pool_name,
            'total_supply': pool_data.total_supply,
            'virtual_price': pool_data.virtual_price,
            'volume_24h': pool_data.volume_24h,
            'fees_24h': pool_data.fees_24h,
            'apy': pool_data.apy
        }
        
        # 代币余额和汇率
        for i, (token, balance, rate) in enumerate(zip(pool_data.tokens, pool_data.balances, pool_data.rates)):
            row[f'{token.lower()}_balance'] = balance
            row[f'{token.lower()}_rate'] = rate
        
        # 计算额外指标
        if len(pool_data.balances) >= 3:  # 3Pool等
            total_balance = sum(pool_data.balances)
            for i, (token, balance) in enumerate(zip(pool_data.tokens, pool_data.balances)):
                row[f'{token.lower()}_ratio'] = balance / total_balance if total_balance > 0 else 0
            
            # 不平衡度计算
            ideal_ratio = 1.0 / len(pool_data.balances)
            deviations = [abs(balance/total_balance - ideal_ratio) for balance in pool_data.balances]
            row['max_imbalance'] = max(deviations) if deviations else 0
        
        return pd.DataFrame([row])

def demo_csv_export():
    """演示CSV导出功能"""
    
    print("📁 Curve数据CSV导出演示")
    print("=" * 50)
    
    # 初始化数据管理器
    manager = CurveDataManager()
    
    print("\n1️⃣ 获取并保存3Pool实时数据...")
    realtime_file = manager.save_real_time_data('3pool', save_csv=True)
    
    print("\n2️⃣ 获取并保存3Pool历史数据...")
    historical_file = manager.save_historical_data('3pool', days=7, save_csv=True)
    
    print("\n3️⃣ 批量保存所有池子数据...")
    batch_results = manager.save_all_pools_data(['3pool', 'frax'], save_csv=True)
    
    print("\n4️⃣ 列出保存的文件...")
    files = manager.list_saved_files()
    for category, file_list in files.items():
        if file_list:
            print(f"📂 {category}: {len(file_list)} 个文件")
            for filename in file_list[:3]:  # 显示前3个
                print(f"   - {filename}")
            if len(file_list) > 3:
                print(f"   ... 还有 {len(file_list) - 3} 个文件")
    
    print("\n5️⃣ 创建汇总报告...")
    report = manager.create_summary_report()
    print(report)
    
    print("\n6️⃣ 测试数据读取...")
    if realtime_file:
        df = manager.load_csv_data(realtime_file)
        if not df.empty:
            print(f"✅ 成功读取数据: {len(df)} 行 x {len(df.columns)} 列")
            print("前几列数据:")
            print(df.head())
    
    print("\n" + "=" * 50)
    print("🎉 CSV导出演示完成!")
    print(f"📁 所有数据保存在: {manager.data_dir.absolute()}")

if __name__ == "__main__":
    demo_csv_export() 