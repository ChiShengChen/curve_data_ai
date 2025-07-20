#!/usr/bin/env python3
"""
🔮 Curve Virtual Price预测模型
基于历史数据预测未来24小时的Virtual Price变化
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
    """Curve池子Virtual Price预测器"""
    
    def __init__(self, pool_name='3pool'):
        self.pool_name = pool_name
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    def load_data(self, file_path=None):
        """加载历史数据"""
        
        if file_path is None:
            file_path = f"free_historical_cache/{self.pool_name}_comprehensive_free_historical_365d.csv"
        
        try:
            self.data = pd.read_csv(file_path)
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            
            print(f"✅ 数据加载成功: {len(self.data)} 条记录")
            print(f"📅 时间范围: {self.data['timestamp'].min()} 到 {self.data['timestamp'].max()}")
            
            return True
            
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return False
    
    def create_features(self):
        """特征工程 - 创建预测特征"""
        
        print("🔧 开始特征工程...")
        
        df = self.data.copy()
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # 1. 滞后特征 (Lag Features)
        for lag in [1, 6, 24, 168]:  # 1个点、6个点(1.5小时)、24个点(6小时)、168个点(42小时/7天)
            df[f'virtual_price_lag_{lag}'] = df['virtual_price'].shift(lag)
        
        # 2. 移动平均特征 (Moving Average)
        for window in [24, 168, 672]:  # 6小时、7天、28天
            df[f'virtual_price_ma_{window}'] = df['virtual_price'].rolling(window).mean()
        
        # 3. 波动率特征 (Volatility)
        for window in [24, 168]:
            df[f'virtual_price_std_{window}'] = df['virtual_price'].rolling(window).std()
            df[f'virtual_price_cv_{window}'] = df[f'virtual_price_std_{window}'] / df[f'virtual_price_ma_{window}']
        
        # 4. 价格变化特征 (Price Change)
        df['virtual_price_change'] = df['virtual_price'].pct_change()
        df['virtual_price_change_abs'] = df['virtual_price_change'].abs()
        
        # 5. 流动性特征 (Liquidity Features)
        df['total_supply_change'] = df['total_supply'].pct_change()
        df['total_supply_ma_24'] = df['total_supply'].rolling(24).mean()
        
        # 6. 余额特征 (Balance Features)
        token_columns = [col for col in df.columns if col.endswith('_balance')]
        if len(token_columns) >= 2:
            df['balance_ratio'] = df[token_columns[0]] / df[token_columns[1]]
            df['balance_imbalance'] = df[token_columns].std(axis=1) / df[token_columns].mean(axis=1)
        
        # 7. 时间特征 (Time Features)
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        
        # 8. 技术指标特征 (Technical Indicators)
        # RSI (相对强弱指数)
        df['price_change_positive'] = df['virtual_price_change'].apply(lambda x: x if x > 0 else 0)
        df['price_change_negative'] = df['virtual_price_change'].apply(lambda x: -x if x < 0 else 0)
        df['rsi_14'] = 100 - (100 / (1 + df['price_change_positive'].rolling(14).mean() / 
                                         df['price_change_negative'].rolling(14).mean()))
        
        # 9. 目标变量 (Target Variable)
        df['target_24h'] = df['virtual_price'].shift(-24)  # 预测24个点后的价格 (6小时后)
        df['target_return_24h'] = (df['target_24h'] / df['virtual_price'] - 1) * 100  # 收益率%
        
        # 删除缺失值
        self.processed_data = df.dropna().reset_index(drop=True)
        
        print(f"✅ 特征工程完成")
        print(f"📊 处理后数据: {len(self.processed_data)} 条记录")
        print(f"🔧 特征数量: {len([col for col in df.columns if col not in ['timestamp', 'pool_address', 'pool_name', 'source', 'target_24h', 'target_return_24h']])} 个")
        
        return self.processed_data
    
    def prepare_training_data(self):
        """准备训练数据"""
        
        # 选择特征列
        exclude_cols = ['timestamp', 'pool_address', 'pool_name', 'source', 'target_24h', 'target_return_24h', 'virtual_price']
        self.feature_columns = [col for col in self.processed_data.columns if col not in exclude_cols]
        
        X = self.processed_data[self.feature_columns].fillna(0)
        y = self.processed_data['target_return_24h'].fillna(0)
        
        # 时间序列分割 (前80%训练，后20%测试)
        split_index = int(len(X) * 0.8)
        
        self.X_train = X.iloc[:split_index]
        self.X_test = X.iloc[split_index:]
        self.y_train = y.iloc[:split_index] 
        self.y_test = y.iloc[split_index:]
        
        # 特征缩放
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
        
        print(f"📊 训练集: {len(self.X_train)} 样本")
        print(f"📊 测试集: {len(self.X_test)} 样本")
        
    def train_model(self):
        """训练预测模型"""
        
        print("🚀 开始训练模型...")
        
        # 使用Random Forest作为基础模型
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(self.X_train_scaled, self.y_train)
        
        print("✅ 模型训练完成")
        
    def evaluate_model(self):
        """评估模型性能"""
        
        print("📈 评估模型性能...")
        
        # 预测
        train_pred = self.model.predict(self.X_train_scaled)
        test_pred = self.model.predict(self.X_test_scaled)
        
        # 计算评估指标
        train_mae = mean_absolute_error(self.y_train, train_pred)
        test_mae = mean_absolute_error(self.y_test, test_pred)
        
        train_rmse = np.sqrt(mean_squared_error(self.y_train, train_pred))
        test_rmse = np.sqrt(mean_squared_error(self.y_test, test_pred))
        
        # 方向准确率
        train_direction_accuracy = np.mean(np.sign(train_pred) == np.sign(self.y_train)) * 100
        test_direction_accuracy = np.mean(np.sign(test_pred) == np.sign(self.y_test)) * 100
        
        print("\n📊 模型评估结果:")
        print(f"{'指标':<15} {'训练集':<12} {'测试集':<12}")
        print("-" * 40)
        print(f"{'MAE':<15} {train_mae:<12.4f} {test_mae:<12.4f}")
        print(f"{'RMSE':<15} {train_rmse:<12.4f} {test_rmse:<12.4f}")
        print(f"{'方向准确率(%)':<15} {train_direction_accuracy:<12.1f} {test_direction_accuracy:<12.1f}")
        
        return {
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_rmse': train_rmse, 
            'test_rmse': test_rmse,
            'train_direction_acc': train_direction_accuracy,
            'test_direction_acc': test_direction_accuracy
        }
    
    def feature_importance(self, top_n=15):
        """显示特征重要性"""
        
        if self.model is None:
            print("❌ 模型未训练")
            return
            
        importances = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n🔝 Top {top_n} 重要特征:")
        print(importances.head(top_n).to_string(index=False))
        
        # 可视化特征重要性
        plt.figure(figsize=(10, 8))
        top_features = importances.head(top_n)
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Feature Importance')
        plt.title(f'{self.pool_name} Virtual Price预测 - 特征重要性')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(f'{self.pool_name}_feature_importance.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return importances
    
    def predict_next_24h(self, current_data=None):
        """预测未来24小时"""
        
        if self.model is None:
            print("❌ 模型未训练")
            return None
            
        if current_data is None:
            # 使用最新的数据点进行预测
            current_data = self.X_test_scaled.iloc[-1:] 
        
        prediction = self.model.predict(current_data)
        
        print(f"🔮 {self.pool_name} 未来6小时Virtual Price预测:")
        print(f"   预期收益率: {prediction[0]:.4f}%")
        
        if prediction[0] > 0:
            print(f"   📈 预测上涨 {prediction[0]:.4f}%")
        else:
            print(f"   📉 预测下跌 {abs(prediction[0]):.4f}%")
            
        return prediction[0]
    
    def plot_predictions(self, last_n_points=200):
        """可视化预测结果"""
        
        if self.model is None:
            print("❌ 模型未训练")
            return
            
        # 获取测试集预测
        test_pred = self.model.predict(self.X_test_scaled)
        
        # 获取最后n个点的数据
        test_data = self.processed_data.iloc[len(self.X_train):].tail(last_n_points)
        actual_returns = self.y_test.tail(last_n_points).values
        pred_returns = test_pred[-last_n_points:]
        
        plt.figure(figsize=(15, 8))
        
        # 绘制实际vs预测收益率
        plt.subplot(2, 1, 1)
        plt.plot(actual_returns, label='实际收益率', alpha=0.7)
        plt.plot(pred_returns, label='预测收益率', alpha=0.7)
        plt.title(f'{self.pool_name} Virtual Price收益率预测 (最近{last_n_points}个时间点)')
        plt.ylabel('收益率 (%)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 绘制预测误差
        plt.subplot(2, 1, 2)
        errors = actual_returns - pred_returns
        plt.plot(errors, color='red', alpha=0.7)
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.title('预测误差')
        plt.ylabel('误差 (%)')
        plt.xlabel('时间点')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.pool_name}_prediction_results.png', dpi=300, bbox_inches='tight')
        plt.show()

def demo_virtual_price_prediction():
    """演示Virtual Price预测"""
    
    print("🔮 Curve Virtual Price预测模型演示")
    print("=" * 50)
    
    # 创建预测器
    predictor = CurveVirtualPricePredictor(pool_name='3pool')
    
    # 加载数据
    if not predictor.load_data():
        print("❌ 数据加载失败，请确保有数据文件")
        return
    
    # 特征工程
    predictor.create_features()
    
    # 准备训练数据
    predictor.prepare_training_data()
    
    # 训练模型
    predictor.train_model()
    
    # 评估模型
    metrics = predictor.evaluate_model()
    
    # 特征重要性分析
    importance = predictor.feature_importance()
    
    # 预测未来24小时
    prediction = predictor.predict_next_24h()
    
    # 可视化结果
    predictor.plot_predictions()
    
    print("\n" + "=" * 50)
    print("🎉 Virtual Price预测模型演示完成!")
    print(f"📊 模型测试准确率: {metrics['test_direction_acc']:.1f}%")
    print(f"📈 预测收益率: {prediction:.4f}%")
    print("=" * 50)

if __name__ == "__main__":
    demo_virtual_price_prediction() 