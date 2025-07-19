#!/usr/bin/env python3
"""
Curve数据CSV功能使用示例
展示如何使用数据管理器保存和读取CSV数据
"""

from data_manager import CurveDataManager
import os

def main():
    print("📁 Curve数据CSV功能使用示例")
    print("=" * 50)
    
    # 1. 初始化数据管理器
    print("🔧 初始化数据管理器...")
    manager = CurveDataManager("my_curve_data")  # 数据将保存在 my_curve_data 目录
    
    # 2. 获取并保存单个池子的实时数据
    print("\n📊 获取3Pool实时数据并保存为CSV...")
    realtime_file = manager.save_real_time_data('3pool', save_csv=True)
    
    if realtime_file:
        print(f"✅ 实时数据保存成功: {realtime_file}")
        
        # 读取刚刚保存的CSV文件
        print("📖 读取保存的CSV文件...")
        df = manager.load_csv_data(realtime_file)
        
        if not df.empty:
            print("🎉 CSV数据内容预览:")
            print(df.to_string(index=False))
            print(f"\n数据维度: {df.shape[0]} 行 x {df.shape[1]} 列")
    
    # 3. 获取历史数据
    print("\n📈 获取7天历史数据...")
    historical_file = manager.save_historical_data('3pool', days=7, save_csv=True)
    
    if historical_file:
        print(f"✅ 历史数据保存成功: {historical_file}")
    
    # 4. 批量保存多个池子
    print("\n🔄 批量保存多个池子...")
    batch_results = manager.save_all_pools_data(['3pool', 'frax'], save_csv=True)
    
    print(f"📊 批量操作结果: 成功保存 {len(batch_results)} 个文件")
    for pool_type, filepath in batch_results.items():
        print(f"  - {pool_type}: {os.path.basename(filepath)}")
    
    # 5. 查看所有保存的文件
    print("\n📂 查看保存的文件...")
    files = manager.list_saved_files()
    
    for category, file_list in files.items():
        if file_list:
            print(f"📁 {category} ({len(file_list)} 个文件):")
            for filename in file_list:
                print(f"  - {filename}")
    
    # 6. 创建汇总报告
    print("\n📋 创建汇总报告...")
    manager.create_summary_report()
    
    # 7. 使用最新数据
    print("\n🔄 获取最新数据...")
    latest_df = manager.get_latest_data('3pool')
    
    if latest_df is not None:
        print("✅ 成功获取最新数据")
        if 'virtual_price' in latest_df.columns:
            virtual_price = latest_df['virtual_price'].iloc[0]
            print(f"当前Virtual Price: {virtual_price:.6f}")
    
    print("\n" + "=" * 50)
    print("🎉 CSV功能演示完成!")
    print("💡 你的数据已保存在 'my_curve_data' 目录下")
    print("📁 目录结构:")
    print("  my_curve_data/")
    print("  ├── real_time/     # 实时数据")
    print("  ├── historical/    # 历史数据") 
    print("  └── backups/       # 备份文件")

if __name__ == "__main__":
    main() 