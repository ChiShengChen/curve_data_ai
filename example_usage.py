#!/usr/bin/env python3
"""
🚀 Curve歷史數據批量獲取系統 - 完整使用示例
演示如何使用擴展後的批量獲取功能
"""

import os
import pandas as pd
from datetime import datetime
from free_historical_data import FreeHistoricalDataCollector, AVAILABLE_POOLS, get_high_priority_pools, get_stable_pools

def example_1_quick_start():
    """🏁 快速開始 - 獲取3pool的歷史數據"""
    
    print("=" * 60)
    print("🏁 示例1: 快速開始")
    print("=" * 60)
    
    collector = FreeHistoricalDataCollector()
    
    # 獲取3pool的7天數據
    print("📊 獲取3pool的7天歷史數據...")
    data = collector.get_comprehensive_free_data(
        pool_name='3pool',
        days=7
    )
    
    if not data.empty:
        print(f"✅ 成功獲取 {len(data)} 條數據")
        print(f"📅 數據時間範圍: {data['timestamp'].min()} 到 {data['timestamp'].max()}")
        print(f"💰 Virtual Price範圍: {data['virtual_price'].min():.6f} - {data['virtual_price'].max():.6f}")
        
        # 保存數據
        data.to_csv('example_3pool_7d.csv', index=False)
        print("💾 數據已保存到: example_3pool_7d.csv")
    else:
        print("❌ 未獲取到數據")

def example_2_batch_by_type():
    """🏊 按類型批量獲取"""
    
    print("\n" + "=" * 60)
    print("🏊 示例2: 按池子類型批量獲取")
    print("=" * 60)
    
    collector = FreeHistoricalDataCollector()
    
    # 獲取所有穩定幣池的數據
    stable_pools = get_stable_pools()
    print(f"📋 找到 {len(stable_pools)} 個穩定幣池")
    
    batch_data = collector.get_batch_historical_data(
        pools_dict=stable_pools,
        days=3,  # 獲取3天數據用於快速測試
        max_concurrent=2,  # 並發數
        delay_between_requests=1  # 請求間延遲
    )
    
    print(f"✅ 批量獲取完成，共 {len(batch_data)} 個池子")
    
    # 顯示各池子數據統計
    for pool_name, data in batch_data.items():
        if not data.empty:
            print(f"  📊 {pool_name:12}: {len(data)} 條數據, VP範圍 {data['virtual_price'].min():.6f}-{data['virtual_price'].max():.6f}")
        else:
            print(f"  ❌ {pool_name:12}: 無數據")

def example_3_comprehensive_analysis():
    """📈 綜合分析 - 高優先級池子對比"""
    
    print("\n" + "=" * 60)
    print("📈 示例3: 高優先級池子綜合分析")
    print("=" * 60)
    
    collector = FreeHistoricalDataCollector()
    
    # 獲取高優先級池子
    high_priority_pools = get_high_priority_pools()
    print(f"🏆 高優先級池子: {list(high_priority_pools.keys())}")
    
    # 批量獲取7天數據
    batch_data = collector.get_batch_historical_data(
        pools_dict=high_priority_pools,
        days=7,
        max_concurrent=3
    )
    
    # 分析數據
    analysis_results = {}
    
    for pool_name, data in batch_data.items():
        if not data.empty and len(data) > 1:
            # 計算統計指標
            vp_start = data['virtual_price'].iloc[0]
            vp_end = data['virtual_price'].iloc[-1] 
            total_return = (vp_end / vp_start - 1) * 100
            volatility = data['virtual_price'].pct_change().std() * 100
            
            analysis_results[pool_name] = {
                'total_return_pct': total_return,
                'volatility_pct': volatility,
                'data_points': len(data),
                'avg_virtual_price': data['virtual_price'].mean()
            }
    
    # 顯示分析結果
    print("\n📊 7天表現分析:")
    print(f"{'池子':<12} {'總收益率(%)':<12} {'波動率(%)':<10} {'數據點':<8} {'平均VP':<12}")
    print("-" * 65)
    
    for pool_name, stats in analysis_results.items():
        print(f"{pool_name:<12} {stats['total_return_pct']:>+10.4f}  {stats['volatility_pct']:>8.4f}  {stats['data_points']:>6d}  {stats['avg_virtual_price']:>10.6f}")

def example_4_custom_selection():
    """🎯 自定義選擇 - 指定池子獲取"""
    
    print("\n" + "=" * 60)
    print("🎯 示例4: 自定義池子選擇")
    print("=" * 60)
    
    collector = FreeHistoricalDataCollector()
    
    # 自定義池子選擇
    custom_pools = {
        '3pool': AVAILABLE_POOLS['3pool'],
        'frax': AVAILABLE_POOLS['frax'], 
        'lusd': AVAILABLE_POOLS['lusd']
    }
    
    print(f"📋 自定義選擇的池子: {list(custom_pools.keys())}")
    
    # 獲取5天數據
    batch_data = collector.get_batch_historical_data(
        pools_dict=custom_pools,
        days=5,
        max_concurrent=2
    )
    
    # 計算相關性分析
    print("\n🔗 池子間Virtual Price相關性分析:")
    
    # 構建價格DataFrame
    price_data = pd.DataFrame()
    for pool_name, data in batch_data.items():
        if not data.empty:
            # 使用timestamp作為索引對齊數據
            temp_df = data.set_index('timestamp')['virtual_price']
            price_data[pool_name] = temp_df
    
    if not price_data.empty:
        # 計算相關性矩陣
        correlation_matrix = price_data.corr()
        
        # 顯示相關性
        print(correlation_matrix.round(4))
        
        # 找出最高相關性
        max_corr = 0
        max_pair = None
        for i in correlation_matrix.index:
            for j in correlation_matrix.columns:
                if i != j:
                    corr_val = correlation_matrix.loc[i, j]
                    if abs(corr_val) > abs(max_corr):
                        max_corr = corr_val
                        max_pair = (i, j)
        
        if max_pair:
            print(f"\n🔗 最高相關性: {max_pair[0]} 與 {max_pair[1]} ({max_corr:.4f})")

def example_5_data_processing():
    """🔄 數據處理 - 清理和轉換"""
    
    print("\n" + "=" * 60)
    print("🔄 示例5: 數據處理和轉換")
    print("=" * 60)
    
    collector = FreeHistoricalDataCollector()
    
    # 獲取3pool數據
    data = collector.get_comprehensive_free_data('3pool', days=10)
    
    if data.empty:
        print("❌ 無法獲取數據")
        return
    
    print(f"📊 原始數據: {len(data)} 條記錄")
    
    # 數據清理和處理
    processed_data = data.copy()
    
    # 1. 添加技術指標
    processed_data['vp_change_pct'] = processed_data['virtual_price'].pct_change() * 100
    processed_data['vp_ma_5'] = processed_data['virtual_price'].rolling(5).mean()
    processed_data['vp_std_5'] = processed_data['virtual_price'].rolling(5).std()
    
    # 2. 添加時間特徵
    processed_data['hour'] = pd.to_datetime(processed_data['timestamp']).dt.hour
    processed_data['day_of_week'] = pd.to_datetime(processed_data['timestamp']).dt.dayofweek
    
    # 3. 刪除缺失值
    processed_data = processed_data.dropna()
    
    print(f"✅ 處理後數據: {len(processed_data)} 條記錄")
    
    # 數據統計
    print("\n📈 Virtual Price統計:")
    vp_stats = processed_data['virtual_price'].describe()
    for stat_name, stat_value in vp_stats.items():
        print(f"  {stat_name:8}: {stat_value:.8f}")
    
    # 價格變化統計
    print("\n📊 價格變化統計:")
    change_stats = processed_data['vp_change_pct'].describe()
    for stat_name, stat_value in change_stats.items():
        print(f"  {stat_name:8}: {stat_value:+.6f}%")
    
    # 保存處理後的數據
    processed_data.to_csv('example_processed_3pool.csv', index=False)
    print("\n💾 處理後的數據已保存到: example_processed_3pool.csv")

def example_6_production_ready():
    """🏭 生產就緒 - 完整的數據管道"""
    
    print("\n" + "=" * 60)
    print("🏭 示例6: 生產級數據管道")
    print("=" * 60)
    
    collector = FreeHistoricalDataCollector()
    
    # 生產級配置
    production_pools = get_high_priority_pools()  # 只處理高優先級池子
    days_to_collect = 30  # 獲取30天數據
    
    print(f"🏭 生產配置:")
    print(f"  📋 池子數量: {len(production_pools)}")
    print(f"  📅 數據天數: {days_to_collect}")
    print(f"  🕐 開始時間: {datetime.now()}")
    
    try:
        # 批量獲取數據
        print("\n🚀 開始批量數據獲取...")
        batch_data = collector.get_batch_historical_data(
            pools_dict=production_pools,
            days=days_to_collect,
            max_concurrent=2,  # 生產環境使用較低並發避免被限制
            delay_between_requests=2  # 增加延遲避免觸發限制
        )
        
        # 數據質量檢查
        print("\n🔍 數據質量檢查:")
        quality_report = {}
        
        for pool_name, data in batch_data.items():
            if not data.empty:
                # 檢查數據完整性
                expected_points = days_to_collect * 4  # 每天4個點
                actual_points = len(data)
                completeness = (actual_points / expected_points) * 100
                
                # 檢查數據異常值
                vp_q1 = data['virtual_price'].quantile(0.25)
                vp_q3 = data['virtual_price'].quantile(0.75)
                vp_iqr = vp_q3 - vp_q1
                outliers = len(data[(data['virtual_price'] < vp_q1 - 1.5*vp_iqr) | 
                                  (data['virtual_price'] > vp_q3 + 1.5*vp_iqr)])
                
                quality_report[pool_name] = {
                    'completeness_pct': completeness,
                    'outliers_count': outliers,
                    'data_points': actual_points
                }
                
                print(f"  📊 {pool_name:12}: 完整度 {completeness:5.1f}%, 異常值 {outliers:2d}個, 數據點 {actual_points:3d}")
        
        # 生成生產報告
        report_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"production_report_{report_time}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"🏭 Curve數據獲取生產報告\n")
            f.write(f"=" * 50 + "\n")
            f.write(f"生成時間: {datetime.now()}\n")
            f.write(f"池子數量: {len(production_pools)}\n") 
            f.write(f"數據天數: {days_to_collect}\n\n")
            
            f.write("數據質量報告:\n")
            f.write("-" * 30 + "\n")
            for pool_name, quality in quality_report.items():
                f.write(f"{pool_name:12}: 完整度 {quality['completeness_pct']:5.1f}%, "
                       f"異常值 {quality['outliers_count']:2d}個, "
                       f"數據點 {quality['data_points']:3d}\n")
        
        print(f"\n📋 生產報告已保存到: {report_filename}")
        
        # 導出批量數據為Excel
        try:
            with pd.ExcelWriter(f'production_data_{report_time}.xlsx') as writer:
                for pool_name, data in batch_data.items():
                    if not data.empty:
                        data.to_excel(writer, sheet_name=pool_name, index=False)
            
            print(f"📊 批量數據已導出為Excel: production_data_{report_time}.xlsx")
        except Exception as e:
            print(f"⚠️  Excel導出失敗: {e}")
        
    except Exception as e:
        print(f"❌ 生產管道執行失敗: {e}")

def main():
    """🎯 主函數 - 執行所有示例"""
    
    print("🚀 Curve批量歷史數據獲取 - 完整使用示例")
    print("=" * 80)
    
    # 檢查緩存目錄
    cache_dir = "free_historical_cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        print(f"📁 創建緩存目錄: {cache_dir}")
    
    try:
        # 執行所有示例
        example_1_quick_start()
        example_2_batch_by_type() 
        example_3_comprehensive_analysis()
        example_4_custom_selection()
        example_5_data_processing()
        example_6_production_ready()
        
        print("\n" + "=" * 80)
        print("🎉 所有示例執行完成！")
        print("=" * 80)
        
        # 顯示生成的文件
        print("\n📄 生成的文件:")
        for filename in os.listdir('.'):
            if filename.startswith('example_') or filename.startswith('production_'):
                file_size = os.path.getsize(filename) / 1024  # KB
                print(f"  📄 {filename} ({file_size:.1f}KB)")
        
    except KeyboardInterrupt:
        print("\n⚠️  用戶中斷執行")
    except Exception as e:
        print(f"\n❌ 執行失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 