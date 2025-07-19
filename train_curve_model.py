#!/usr/bin/env python3
"""
Curve智能重新平衡模型训练脚本
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from tqdm import tqdm
import argparse
import os
from datetime import datetime, timedelta
from typing import Tuple

from curve_rebalancer import CurvePoolPredictor, CurveDataCollector
from pathlib import Path

class CurveDataset(Dataset):
    """Curve数据集类"""
    
    def __init__(self, data: np.ndarray, targets: dict, seq_length: int = 24):
        self.data = data
        self.targets = targets
        self.seq_length = seq_length
        
    def __len__(self):
        return len(self.data) - self.seq_length
    
    def __getitem__(self, idx):
        # 输入序列
        x = self.data[idx:idx + self.seq_length]
        
        # 目标值（预测下一个时间点的状态）
        target_idx = idx + self.seq_length
        y = {
            'pool_balance': self.targets['pool_balance'][target_idx],
            'apy': self.targets['apy'][target_idx],
            'price_deviation': self.targets['price_deviation'][target_idx],
            'volume': self.targets['volume'][target_idx]
        }
        
        return torch.FloatTensor(x), y

def generate_synthetic_data(num_samples: int = 10000, seq_length: int = 24):
    """生成合成的Curve池数据"""
    
    print(f"Generating {num_samples} synthetic data samples...")
    
    # 时间序列特征
    dates = pd.date_range(start='2023-01-01', periods=num_samples, freq='H')
    
    # 基础特征
    data = {}
    
    # USDC, USDT, DAI 余额 (相互关联)
    base_balance = 1000000
    usdc_trend = np.random.normal(0, 0.001, num_samples).cumsum()
    usdt_trend = np.random.normal(0, 0.001, num_samples).cumsum()
    dai_trend = -(usdc_trend + usdt_trend).astype(float) + np.random.normal(0, 0.0005, num_samples).cumsum()
    
    data['usdc_balance'] = base_balance * (1 + usdc_trend + 0.1 * np.sin(np.arange(num_samples) * 2 * np.pi / (24 * 7)))
    data['usdt_balance'] = base_balance * (1 + usdt_trend + 0.08 * np.cos(np.arange(num_samples) * 2 * np.pi / (24 * 7)))
    data['dai_balance'] = base_balance * (1 + dai_trend + 0.06 * np.sin(np.arange(num_samples) * 2 * np.pi / (24 * 30)))
    
    # Virtual price (通常稳定增长)
    data['virtual_price'] = 1.0 + np.random.normal(0, 0.0001, num_samples).cumsum() + 0.0001 * np.arange(num_samples)
    
    # 交易量 (有周期性和随机性)
    volume_base = np.exp(np.random.normal(11, 1, num_samples))  # log-normal分布
    volume_weekly = 0.3 * np.sin(np.arange(num_samples) * 2 * np.pi / (24 * 7))  # 周周期
    volume_daily = 0.2 * np.sin(np.arange(num_samples) * 2 * np.pi / 24)  # 日周期
    data['volume_24h'] = volume_base * (1 + volume_weekly + volume_daily)
    
    df = pd.DataFrame(data, index=dates)
    
    # 计算目标变量
    targets = {}
    
    # 池子余额比例
    total_balance = df['usdc_balance'] + df['usdt_balance'] + df['dai_balance']
    targets['pool_balance'] = np.stack([
        df['usdc_balance'] / total_balance,
        df['usdt_balance'] / total_balance,
        df['dai_balance'] / total_balance
    ], axis=1)
    
    # APY (基于交易量和余额)
    targets['apy'] = (0.02 + 0.03 * (df['volume_24h'] / df['volume_24h'].mean()) / 
                     (total_balance / total_balance.mean())).values
    targets['apy'] = np.clip(targets['apy'], 0, 0.2)  # 限制在0-20%
    
    # 价格偏离 (基于余额不平衡)
    ideal_balance = 1/3
    usdc_deviation = (df['usdc_balance'] / total_balance) - ideal_balance
    usdt_deviation = (df['usdt_balance'] / total_balance) - ideal_balance
    dai_deviation = (df['dai_balance'] / total_balance) - ideal_balance
    
    targets['price_deviation'] = np.stack([
        usdc_deviation * 0.01,  # 转换为价格偏离
        usdt_deviation * 0.01,
        dai_deviation * 0.01
    ], axis=1)
    
    # 交易量
    targets['volume'] = df['volume_24h'].values
    
    return df[['usdc_balance', 'usdt_balance', 'dai_balance', 'virtual_price', 'volume_24h']].values, targets

def load_real_csv_data(csv_data_dir: str) -> Tuple[np.ndarray, dict]:
    """从CSV文件加载真实数据"""
    
    data_dir = Path(csv_data_dir)
    historical_dir = data_dir / "historical"
    
    print(f"Loading real data from {historical_dir}...")
    
    if not historical_dir.exists():
        print(f"❌ 数据目录不存在: {historical_dir}")
        print("请先运行 python example_csv_usage.py 获取数据")
        return generate_synthetic_data(10000, 24)
    
    # 查找3Pool的历史数据文件
    csv_files = list(historical_dir.glob("3pool_historical_*.csv"))
    
    if not csv_files:
        print("❌ 未找到3Pool历史数据CSV文件")
        print("请先运行 python example_csv_usage.py 获取数据")
        return generate_synthetic_data(10000, 24)
    
    # 使用最新的CSV文件
    latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"📊 使用数据文件: {latest_csv.name}")
    
    try:
        df = pd.read_csv(latest_csv)
        print(f"✅ 成功加载 {len(df)} 条真实数据记录")
        
        # 检查必要的列
        required_cols = ['usdc_balance', 'usdt_balance', 'dai_balance', 'virtual_price', 'volume_24h']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"❌ 缺少必要列: {missing_cols}")
            print("使用合成数据代替...")
            return generate_synthetic_data(10000, 24)
        
        # 数据预处理
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        # 检查数据质量
        null_check = df[required_cols].isnull().sum().sum()
        if null_check > 0:
            print("⚠️  发现缺失值，进行填充...")
            df[required_cols] = df[required_cols].ffill().bfill()
        
        # 提取特征
        X = df[required_cols].values
        
        # 构造目标变量 (类似合成数据的方式)
        targets = {}
        
        # 池子余额比例
        total_balance = df['usdc_balance'] + df['usdt_balance'] + df['dai_balance']
        targets['pool_balance'] = np.stack([
            df['usdc_balance'] / total_balance,
            df['usdt_balance'] / total_balance, 
            df['dai_balance'] / total_balance
        ], axis=1)
        
        # APY (如果有的话，否则从volume估算)
        if 'apy' in df.columns:
            targets['apy'] = df['apy'].values
        else:
            # 基于交易量估算APY
            volume_normalized = df['volume_24h'] / df['volume_24h'].mean()
            tvl_normalized = total_balance / total_balance.mean()
            targets['apy'] = np.clip(0.02 + 0.03 * volume_normalized / tvl_normalized, 0, 0.2)
        
        # 价格偏离 (基于余额比例计算)
        ideal_balance = 1/3
        usdc_deviation = (df['usdc_balance'] / total_balance) - ideal_balance
        usdt_deviation = (df['usdt_balance'] / total_balance) - ideal_balance  
        dai_deviation = (df['dai_balance'] / total_balance) - ideal_balance
        
        targets['price_deviation'] = np.stack([
            usdc_deviation * 0.01,
            usdt_deviation * 0.01,
            dai_deviation * 0.01
        ], axis=1)
        
        # 交易量
        targets['volume'] = df['volume_24h'].values
        
        print("📊 真实数据统计:")
        print(f"  - 数据点数: {len(X)}")
        print(f"  - 平均Virtual Price: {df['virtual_price'].mean():.6f}")
        print(f"  - 平均日交易量: ${df['volume_24h'].mean():,.0f}")
        apy_array = np.array(targets['apy'])
        print(f"  - APY范围: {apy_array.min():.2%} - {apy_array.max():.2%}")
        
        return X, targets
        
    except Exception as e:
        print(f"❌ 加载CSV数据失败: {e}")
        print("使用合成数据代替...")
        return generate_synthetic_data(10000, 24)

def train_model(args):
    """训练模型"""
    
    print("=== Curve智能重新平衡模型训练 ===")
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # 生成或加载数据
    if args.use_real_data:
        print("🌐 使用真实CSV数据进行训练...")
        X, targets = load_real_csv_data(args.csv_data_dir)
    else:
        print("🎲 使用合成数据进行训练...")
        X, targets = generate_synthetic_data(args.num_samples, args.seq_length)
    
    # 数据标准化
    scaler_X = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)
    
    # 分割数据集
    train_size = int(0.8 * len(X_scaled))
    val_size = int(0.1 * len(X_scaled))
    
    X_train = X_scaled[:train_size]
    X_val = X_scaled[train_size:train_size + val_size]
    X_test = X_scaled[train_size + val_size:]
    
    # 分割目标
    targets_train = {k: v[:train_size] for k, v in targets.items()}
    targets_val = {k: v[train_size:train_size + val_size] for k, v in targets.items()}
    targets_test = {k: v[train_size + val_size:] for k, v in targets.items()}
    
    # 创建数据集
    train_dataset = CurveDataset(X_train, targets_train, args.seq_length)
    val_dataset = CurveDataset(X_val, targets_val, args.seq_length)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    
    print(f"Training samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    
    # 创建模型
    model = CurvePoolPredictor(
        input_dim=X.shape[1],
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers
    ).to(device)
    
    # 优化器
    optimizer = optim.Adam(model.parameters(), lr=args.learning_rate, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.7)
    
    # 损失函数
    mse_loss = nn.MSELoss()
    
    # 训练历史
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')
    
    print("\n开始训练...")
    for epoch in range(args.epochs):
        # 训练阶段
        model.train()
        epoch_train_loss = 0.0
        
        train_pbar = tqdm(train_loader, desc=f'Epoch {epoch+1}/{args.epochs} [Train]', leave=False)
        for batch_x, batch_y in train_pbar:
            batch_x = batch_x.to(device)
            
            # 移动目标到设备
            batch_y_device = {}
            for key, value in batch_y.items():
                if key == 'pool_balance' or key == 'price_deviation':
                    batch_y_device[key] = value.float().to(device)
                else:
                    batch_y_device[key] = value.float().unsqueeze(1).to(device)
            
            optimizer.zero_grad()
            
            # 前向传播
            predictions = model(batch_x)
            
            # 计算损失
            loss = 0
            loss += mse_loss(predictions['pool_balance'], batch_y_device['pool_balance'])
            loss += mse_loss(predictions['apy'], batch_y_device['apy'])
            loss += mse_loss(predictions['price_deviation'], batch_y_device['price_deviation'])
            loss += mse_loss(predictions['volume'], batch_y_device['volume'])
            
            # 反向传播
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            epoch_train_loss += loss.item()
            train_pbar.set_postfix({'loss': f'{loss.item():.6f}'})
        
        # 验证阶段
        model.eval()
        epoch_val_loss = 0.0
        
        with torch.no_grad():
            val_pbar = tqdm(val_loader, desc=f'Epoch {epoch+1}/{args.epochs} [Val]', leave=False)
            for batch_x, batch_y in val_pbar:
                batch_x = batch_x.to(device)
                
                batch_y_device = {}
                for key, value in batch_y.items():
                    if key == 'pool_balance' or key == 'price_deviation':
                        batch_y_device[key] = value.float().to(device)
                    else:
                        batch_y_device[key] = value.float().unsqueeze(1).to(device)
                
                predictions = model(batch_x)
                
                val_loss = 0
                val_loss += mse_loss(predictions['pool_balance'], batch_y_device['pool_balance'])
                val_loss += mse_loss(predictions['apy'], batch_y_device['apy'])
                val_loss += mse_loss(predictions['price_deviation'], batch_y_device['price_deviation'])
                val_loss += mse_loss(predictions['volume'], batch_y_device['volume'])
                
                epoch_val_loss += val_loss.item()
                val_pbar.set_postfix({'val_loss': f'{val_loss.item():.6f}'})
        
        avg_train_loss = epoch_train_loss / len(train_loader)
        avg_val_loss = epoch_val_loss / len(val_loader)
        
        train_losses.append(avg_train_loss)
        val_losses.append(avg_val_loss)
        
        scheduler.step(avg_val_loss)
        
        print(f'Epoch {epoch+1:3d}: Train Loss={avg_train_loss:.6f}, Val Loss={avg_val_loss:.6f}')
        
        # 保存最佳模型
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': avg_train_loss,
                'val_loss': avg_val_loss,
                'scaler': scaler_X
            }, 'best_curve_model.pth')
            print(f"  → 保存最佳模型 (val_loss: {best_val_loss:.6f})")
    
    # 绘制训练曲线
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label='Training Loss', alpha=0.7)
    plt.plot(val_losses, label='Validation Loss', alpha=0.7)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.title('Curve Model Training History')
    plt.grid(True, alpha=0.3)
    plt.savefig('training_curve.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\n训练完成! 最佳验证损失: {best_val_loss:.6f}")
    print(f"模型已保存到: best_curve_model.pth")
    print(f"训练曲线已保存到: training_curve.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='训练Curve智能重新平衡模型')
    
    parser.add_argument('--num_samples', type=int, default=10000, 
                       help='生成的合成数据样本数量')
    parser.add_argument('--seq_length', type=int, default=24, 
                       help='输入序列长度（小时）')
    parser.add_argument('--batch_size', type=int, default=64, 
                       help='批次大小')
    parser.add_argument('--epochs', type=int, default=50, 
                       help='训练轮数')
    parser.add_argument('--learning_rate', type=float, default=0.001, 
                       help='学习率')
    parser.add_argument('--hidden_dim', type=int, default=128, 
                       help='隐藏层维度')
    parser.add_argument('--num_layers', type=int, default=2, 
                       help='LSTM层数')
    parser.add_argument('--use-real-data', action='store_true',
                       help='使用真实CSV数据而不是合成数据')
    parser.add_argument('--csv-data-dir', type=str, default='curve_data',
                       help='CSV数据目录路径')
    
    args = parser.parse_args()
    
    train_model(args) 