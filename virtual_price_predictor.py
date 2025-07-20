#!/usr/bin/env python3
"""
🔮 Curve Virtual Price預測模型
基於歷史數據預測未來24小時的Virtual Price變化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class CurveVirtualPricePredictor:
    """Curve池子Virtual Price預測器"""
    
    def __init__(self, pool_name='3pool'):
        self.pool_name = pool_name
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    def load_data(self, file_path=None):
        """載入歷史數據"""
        
        if file_path is None:
            file_path = f"free_historical_cache/{self.pool_name}_comprehensive_free_historical_365d.csv"
        
        try:
            self.data = pd.read_csv(file_path)
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            
            print(f"✅ 數據載入成功: {len(self.data)} 條記錄")
            print(f"📅 時間範圍: {self.data['timestamp'].min()} 到 {self.data['timestamp'].max()}")
            
            return True
            
        except Exception as e:
            print(f"❌ 數據載入失敗: {e}")
            return False
    
    def create_features(self):
        """特徵工程 - 創建預測特徵"""
        
        print("🔧 開始特徵工程...")
        
        df = self.data.copy()
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # 1. 滯後特徵 (Lag Features)
        for lag in [1, 6, 24, 168]:  # 1個點、6個點(1.5小時)、24個點(6小時)、168個點(42小時/7天)
            df[f'virtual_price_lag_{lag}'] = df['virtual_price'].shift(lag)
        
        # 2. 移動平均特徵 (Moving Average)
        for window in [24, 168, 672]:  # 6小時、7天、28天
            df[f'virtual_price_ma_{window}'] = df['virtual_price'].rolling(window).mean()
        
        # 3. 波動率特徵 (Volatility)
        for window in [24, 168]:
            df[f'virtual_price_std_{window}'] = df['virtual_price'].rolling(window).std()
            df[f'virtual_price_cv_{window}'] = df[f'virtual_price_std_{window}'] / df[f'virtual_price_ma_{window}']
        
        # 4. 價格變化特徵 (Price Change)
        df['virtual_price_change'] = df['virtual_price'].pct_change()
        df['virtual_price_change_abs'] = df['virtual_price_change'].abs()
        
        # 5. 流動性特徵 (Liquidity Features)
        df['total_supply_change'] = df['total_supply'].pct_change()
        df['total_supply_ma_24'] = df['total_supply'].rolling(24).mean()
        
        # 6. 餘額特徵 (Balance Features)
        token_columns = [col for col in df.columns if col.endswith('_balance')]
        if len(token_columns) >= 2:
            df['balance_ratio'] = df[token_columns[0]] / df[token_columns[1]]
            df['balance_imbalance'] = df[token_columns].std(axis=1) / df[token_columns].mean(axis=1)
        
        # 7. 時間特徵 (Time Features)
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        
        # 8. 技術指標特徵 (Technical Indicators)
        # RSI (相對強弱指數)
        df['price_change_positive'] = df['virtual_price_change'].apply(lambda x: x if x > 0 else 0)
        df['price_change_negative'] = df['virtual_price_change'].apply(lambda x: -x if x < 0 else 0)
        df['rsi_14'] = 100 - (100 / (1 + df['price_change_positive'].rolling(14).mean() / 
                                         df['price_change_negative'].rolling(14).mean()))
        
        # 9. 目標變數 (Target Variable)
        df['target_24h'] = df['virtual_price'].shift(-24)  # 預測24個點後的價格 (6小時後)
        df['target_return_24h'] = (df['target_24h'] / df['virtual_price'] - 1) * 100  # 收益率%
        
        # 刪除缺失值
        self.processed_data = df.dropna().reset_index(drop=True)
        
        print(f"✅ 特徵工程完成")
        print(f"📊 處理後數據: {len(self.processed_data)} 條記錄")
        print(f"🔧 特徵數量: {len([col for col in df.columns if col not in ['timestamp', 'pool_address', 'pool_name', 'source', 'target_24h', 'target_return_24h']])} 個")
        
        return self.processed_data
    
    def prepare_training_data(self):
        """準備訓練數據"""
        
        # 選擇特徵欄
        exclude_cols = ['timestamp', 'pool_address', 'pool_name', 'source', 'target_24h', 'target_return_24h', 'virtual_price']
        self.feature_columns = [col for col in self.processed_data.columns if col not in exclude_cols]
        
        X = self.processed_data[self.feature_columns].fillna(0)
        y = self.processed_data['target_return_24h'].fillna(0)
        
        # 時間序列分割 (前80%訓練，後20%測試)
        split_index = int(len(X) * 0.8)
        
        self.X_train = X.iloc[:split_index]
        self.X_test = X.iloc[split_index:]
        self.y_train = y.iloc[:split_index] 
        self.y_test = y.iloc[split_index:]
        
        # 特徵縮放
        self.X_train_scaled = pd.DataFrame(
            self.scaler.fit_transform(self.X_train),
            columns=self.X_train.columns,
            index=self.X_train.index
        )
        
        self.X_test_scaled = pd.DataFrame(
            self.scaler.transform(self.X_test),
            columns=self.X_test.columns,
            index=self.X_test.index
        )
        
        print(f"📊 訓練集: {len(self.X_train)} 樣本")
        print(f"📊 測試集: {len(self.X_test)} 樣本")
        
    def train_model(self):
        """訓練預測模型"""
        
        print("🚀 開始訓練模型...")
        
        # 使用Random Forest作為基礎模型
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(self.X_train_scaled, self.y_train)
        
        print("✅ 模型訓練完成")
        
    def evaluate_model(self):
        """評估模型性能"""
        
        print("📈 評估模型性能...")
        
        # 預測
        train_pred = self.model.predict(self.X_train_scaled)
        test_pred = self.model.predict(self.X_test_scaled)
        
        # 計算評估指標
        train_mae = mean_absolute_error(self.y_train, train_pred)
        test_mae = mean_absolute_error(self.y_test, test_pred)
        
        train_rmse = np.sqrt(mean_squared_error(self.y_train, train_pred))
        test_rmse = np.sqrt(mean_squared_error(self.y_test, test_pred))
        
        # 方向準確率
        train_direction_accuracy = np.mean(np.sign(train_pred) == np.sign(self.y_train)) * 100
        test_direction_accuracy = np.mean(np.sign(test_pred) == np.sign(self.y_test)) * 100
        
        print("\n📊 模型評估結果:")
        print(f"{'指標':<15} {'訓練集':<12} {'測試集':<12}")
        print("-" * 40)
        print(f"{'MAE':<15} {train_mae:<12.4f} {test_mae:<12.4f}")
        print(f"{'RMSE':<15} {train_rmse:<12.4f} {test_rmse:<12.4f}")
        print(f"{'方向準確率(%)':<15} {train_direction_accuracy:<12.1f} {test_direction_accuracy:<12.1f}")
        
        return {
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_rmse': train_rmse, 
            'test_rmse': test_rmse,
            'train_direction_acc': train_direction_accuracy,
            'test_direction_acc': test_direction_accuracy
        }
    
    def feature_importance(self, top_n=15):
        """顯示特徵重要性"""
        
        if self.model is None:
            print("❌ 模型未訓練")
            return
            
        importances = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n🔝 Top {top_n} 重要特徵:")
        print(importances.head(top_n).to_string(index=False))
        
        # 可視化特徵重要性
        plt.figure(figsize=(10, 8))
        top_features = importances.head(top_n)
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Feature Importance')
        plt.title(f'{self.pool_name} Virtual Price預測 - 特徵重要性')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(f'{self.pool_name}_feature_importance.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return importances
    
    def predict_next_24h(self, current_data=None):
        """預測未來24小時"""
        
        if self.model is None:
            print("❌ 模型未訓練")
            return None
            
        if current_data is None:
            # 使用最新的數據點進行預測
            current_data = self.X_test_scaled.iloc[-1:] 
        
        prediction = self.model.predict(current_data)
        
        print(f"🔮 {self.pool_name} 未來6小時Virtual Price預測:")
        print(f"   預期收益率: {prediction[0]:.4f}%")
        
        if prediction[0] > 0:
            print(f"   📈 預測上漲 {prediction[0]:.4f}%")
        else:
            print(f"   📉 預測下跌 {abs(prediction[0]):.4f}%")
            
        return prediction[0]
    
    def plot_predictions(self, last_n_points=200):
        """可視化預測結果"""
        
        if self.model is None:
            print("❌ 模型未訓練")
            return
            
        # 獲取測試集預測
        test_pred = self.model.predict(self.X_test_scaled)
        
        # 獲取最後n個點的數據
        test_data = self.processed_data.iloc[len(self.X_train):].tail(last_n_points)
        actual_returns = self.y_test.tail(last_n_points).values
        pred_returns = test_pred[-last_n_points:]
        
        plt.figure(figsize=(15, 8))
        
        # 繪制實際vs預測收益率
        plt.subplot(2, 1, 1)
        plt.plot(actual_returns, label='實際收益率', alpha=0.7)
        plt.plot(pred_returns, label='預測收益率', alpha=0.7)
        plt.title(f'{self.pool_name} Virtual Price收益率預測 (最近{last_n_points}個時間點)')
        plt.ylabel('收益率 (%)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 繪制預測誤差
        plt.subplot(2, 1, 2)
        errors = actual_returns - pred_returns
        plt.plot(errors, color='red', alpha=0.7)
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.title('預測誤差')
        plt.ylabel('誤差 (%)')
        plt.xlabel('時間點')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.pool_name}_prediction_results.png', dpi=300, bbox_inches='tight')
        plt.show()

def demo_virtual_price_prediction():
    """演示Virtual Price預測"""
    
    print("🔮 Curve Virtual Price預測模型演示")
    print("=" * 50)
    
    # 創建預測器
    predictor = CurveVirtualPricePredictor(pool_name='3pool')
    
    # 載入數據
    if not predictor.load_data():
        print("❌ 數據載入失敗，請確保有數據檔案")
        return
    
    # 特徵工程
    predictor.create_features()
    
    # 準備訓練數據
    predictor.prepare_training_data()
    
    # 訓練模型
    predictor.train_model()
    
    # 評估模型
    metrics = predictor.evaluate_model()
    
    # 特徵重要性分析
    importance = predictor.feature_importance()
    
    # 預測未來24小時
    prediction = predictor.predict_next_24h()
    
    # 可視化結果
    predictor.plot_predictions()
    
    print("\n" + "=" * 50)
    print("🎉 Virtual Price預測模型演示完成!")
    print(f"📊 模型測試準確率: {metrics['test_direction_acc']:.1f}%")
    print(f"📈 預測收益率: {prediction:.4f}%")
    print("=" * 50)

if __name__ == "__main__":
    demo_virtual_price_prediction() 