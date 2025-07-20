#!/usr/bin/env python3
"""
🌊 Curve多池子預測系統
同時預測多個池子的Virtual Price，找出最佳投資機會
"""

import pandas as pd
import numpy as np
from virtual_price_predictor import CurveVirtualPricePredictor
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

class MultiPoolPredictor:
    """多池子預測管理器"""
    
    def __init__(self, pool_names=None):
        if pool_names is None:
            # 預設選擇有數據的高優先級池子
            self.pool_names = ['3pool', 'frax', 'lusd', 'steth', 'tricrypto']
        else:
            self.pool_names = pool_names
            
        self.predictors = {}
        self.predictions = {}
        self.model_performance = {}
        
    def check_data_availability(self):
        """檢查數據可用性"""
        
        available_pools = []
        
        for pool_name in self.pool_names:
            file_path = f"free_historical_cache/{pool_name}_comprehensive_free_historical_365d.csv"
            
            if os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path, nrows=5)
                    if len(df) > 0:
                        available_pools.append(pool_name)
                        print(f"✅ {pool_name:12}: 數據可用")
                    else:
                        print(f"❌ {pool_name:12}: 數據為空")
                except:
                    print(f"❌ {pool_name:12}: 數據讀取失敗")
            else:
                print(f"❌ {pool_name:12}: 檔案不存在")
        
        self.available_pools = available_pools
        print(f"\n📊 可用池子: {len(available_pools)}/{len(self.pool_names)}")
        
        return available_pools
    
    def train_all_models(self, quiet=True):
        """訓練所有池子的預測模型"""
        
        print("🚀 開始訓練多池子預測模型...")
        print("=" * 50)
        
        for pool_name in self.available_pools:
            print(f"\n🔄 訓練 {pool_name} 預測模型...")
            
            try:
                # 創建預測器
                predictor = CurveVirtualPricePredictor(pool_name=pool_name)
                
                # 載入數據並訓練
                if predictor.load_data():
                    predictor.create_features()
                    predictor.prepare_training_data()
                    predictor.train_model()
                    
                    # 評估模型
                    if not quiet:
                        metrics = predictor.evaluate_model()
                    else:
                        # 靜默評估
                        train_pred = predictor.model.predict(predictor.X_train_scaled)
                        test_pred = predictor.model.predict(predictor.X_test_scaled)
                        
                        test_mae = np.mean(np.abs(predictor.y_test - test_pred))
                        direction_accuracy = np.mean(np.sign(test_pred) == np.sign(predictor.y_test)) * 100
                        
                        metrics = {
                            'test_mae': test_mae,
                            'test_direction_acc': direction_accuracy
                        }
                    
                    # 存儲模型和性能
                    self.predictors[pool_name] = predictor
                    self.model_performance[pool_name] = metrics
                    
                    print(f"✅ {pool_name} 訓練完成 - 準確率: {metrics['test_direction_acc']:.1f}%")
                    
                else:
                    print(f"❌ {pool_name} 數據載入失敗")
                    
            except Exception as e:
                print(f"❌ {pool_name} 訓練失敗: {str(e)[:50]}...")
        
        print(f"\n✅ 多池子模型訓練完成!")
        print(f"📊 成功訓練: {len(self.predictors)}/{len(self.available_pools)} 個模型")
    
    def generate_predictions(self):
        """生成所有池子的預測"""
        
        print("\n🔮 生成多池子預測...")
        
        for pool_name, predictor in self.predictors.items():
            try:
                prediction = predictor.predict_next_24h()
                self.predictions[pool_name] = prediction
                
            except Exception as e:
                print(f"❌ {pool_name} 預測失敗: {e}")
                self.predictions[pool_name] = None
        
        return self.predictions
    
    def rank_investment_opportunities(self):
        """排序投資機會"""
        
        if not self.predictions:
            self.generate_predictions()
        
        # 創建排名數據
        ranking_data = []
        
        for pool_name, prediction in self.predictions.items():
            if prediction is not None:
                performance = self.model_performance.get(pool_name, {})
                
                ranking_data.append({
                    'Pool': pool_name,
                    'Predicted_Return_%': prediction,
                    'Model_Accuracy_%': performance.get('test_direction_acc', 0),
                    'MAE': performance.get('test_mae', 0),
                    'Confidence_Score': self._calculate_confidence_score(prediction, performance)
                })
        
        # 創建DataFrame並排序
        ranking_df = pd.DataFrame(ranking_data)
        ranking_df = ranking_df.sort_values('Confidence_Score', ascending=False)
        
        print("\n🏆 投資機會排名:")
        print("=" * 70)
        print(ranking_df.round(3).to_string(index=False))
        
        return ranking_df
    
    def _calculate_confidence_score(self, prediction, performance):
        """計算置信度分數"""
        
        # 綜合考慮預測收益率和模型準確率
        accuracy = performance.get('test_direction_acc', 50) / 100
        mae = performance.get('test_mae', 10)
        
        # 置信度 = (模型準確率 * 預測收益率絕對值) / MAE
        confidence = (accuracy * abs(prediction)) / max(mae, 0.1)
        
        return confidence
    
    def plot_prediction_comparison(self):
        """可視化預測比較"""
        
        if not self.predictions:
            return
        
        # 準備數據
        pools = list(self.predictions.keys())
        predictions = [self.predictions[pool] for pool in pools if self.predictions[pool] is not None]
        accuracies = [self.model_performance[pool]['test_direction_acc'] 
                     for pool in pools if self.predictions[pool] is not None]
        
        pools = [pool for pool in pools if self.predictions[pool] is not None]
        
        if len(pools) == 0:
            print("❌ 沒有可用的預測數據")
            return
        
        # 創建圖表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 預測收益率對比
        colors = ['green' if p > 0 else 'red' for p in predictions]
        bars1 = ax1.bar(pools, predictions, color=colors, alpha=0.7)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax1.set_title('🔮 各池子未來6小時預測收益率', fontsize=14, fontweight='bold')
        ax1.set_ylabel('預測收益率 (%)')
        ax1.grid(True, alpha=0.3)
        
        # 添加數值標籤
        for bar, pred in zip(bars1, predictions):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height >= 0 else -0.1),
                    f'{pred:.2f}%', ha='center', va='bottom' if height >= 0 else 'top')
        
        # 模型準確率對比
        bars2 = ax2.bar(pools, accuracies, color='blue', alpha=0.7)
        ax2.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='隨機水準(50%)')
        ax2.set_title('📊 各池子模型預測準確率', fontsize=14, fontweight='bold')
        ax2.set_ylabel('方向準確率 (%)')
        ax2.set_xlabel('Curve池子')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # 添加數值標籤
        for bar, acc in zip(bars2, accuracies):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{acc:.1f}%', ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('multi_pool_predictions.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_investment_report(self):
        """生成投資報告"""
        
        ranking = self.rank_investment_opportunities()
        
        if len(ranking) == 0:
            print("❌ 沒有可用的預測數據")
            return
        
        report = []
        report.append("=" * 60)
        report.append("📊 CURVE多池子投資分析報告")
        report.append("=" * 60)
        report.append(f"🕐 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"🏊 分析池子: {len(ranking)} 個")
        report.append("")
        
        # Top 3 推薦
        report.append("🏆 TOP 3 投資推薦:")
        report.append("-" * 30)
        
        for i, row in ranking.head(3).iterrows():
            pool = row['Pool']
            pred_return = row['Predicted_Return_%']
            accuracy = row['Model_Accuracy_%']
            confidence = row['Confidence_Score']
            
            rank = len([r for r in ranking.index if r < i]) + 1
            
            if pred_return > 0:
                trend = f"📈 預測上漲 {pred_return:.3f}%"
            else:
                trend = f"📉 預測下跌 {abs(pred_return):.3f}%"
            
            report.append(f"#{rank} {pool.upper()}")
            report.append(f"   {trend}")
            report.append(f"   模型準確率: {accuracy:.1f}%")
            report.append(f"   置信度: {confidence:.2f}")
            report.append("")
        
        # 風險提示
        report.append("⚠️  風險提示:")
        report.append("-" * 15)
        report.append("• 預測僅基於歷史數據，不構成投資建議")
        report.append("• DeFi投資存在智能合約、無常損失等風險")
        report.append("• 建議分散投資，控制單一池子風險敞口")
        report.append("• 密切關注Gas費用對收益的影響")
        
        report.append("")
        report.append("=" * 60)
        
        # 打印報告
        full_report = "\n".join(report)
        print(full_report)
        
        # 保存報告
        with open('curve_investment_report.txt', 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        print("💾 投資報告已保存到: curve_investment_report.txt")
        
        return full_report
    
    def compare_with_historical_performance(self):
        """與歷史表現比較"""
        
        if not self.predictors:
            print("❌ 沒有訓練好的模型")
            return
        
        print("\n📈 歷史表現分析:")
        print("-" * 40)
        
        for pool_name, predictor in self.predictors.items():
            try:
                # 獲取最近30天的實際價格變化
                recent_data = predictor.processed_data.tail(30*4)  # 30天*4點/天
                
                if len(recent_data) > 0:
                    total_return = (recent_data['virtual_price'].iloc[-1] / 
                                  recent_data['virtual_price'].iloc[0] - 1) * 100
                    
                    volatility = recent_data['virtual_price_change'].std() * 100
                    
                    print(f"{pool_name:12}: 近30天收益 {total_return:+6.2f}%, 波動率 {volatility:.2f}%")
                
            except Exception as e:
                print(f"{pool_name:12}: 歷史分析失敗")

def demo_multi_pool_prediction():
    """演示多池子預測系統"""
    
    print("🌊 Curve多池子預測系統演示")
    print("=" * 60)
    
    # 創建多池子預測器
    predictor = MultiPoolPredictor()
    
    # 檢查數據可用性
    available_pools = predictor.check_data_availability()
    
    if len(available_pools) == 0:
        print("❌ 沒有可用的數據檔案")
        return
    
    # 訓練所有模型
    predictor.train_all_models(quiet=True)
    
    # 生成預測
    predictions = predictor.generate_predictions()
    
    # 投資機會排名
    ranking = predictor.rank_investment_opportunities()
    
    # 可視化比較
    predictor.plot_prediction_comparison()
    
    # 歷史表現比較
    predictor.compare_with_historical_performance()
    
    # 生成投資報告
    predictor.generate_investment_report()
    
    print("\n🎉 多池子預測系統演示完成!")

if __name__ == "__main__":
    demo_multi_pool_prediction() 