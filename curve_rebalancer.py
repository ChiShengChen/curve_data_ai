import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Tuple, Optional
import pandas as pd
from dataclasses import dataclass
try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("Web3 not available. Install with: pip install web3")
import requests
import time

@dataclass
class CurvePoolState:
    """Curve池状态数据结构"""
    pool_address: str
    tokens: List[str]
    balances: List[float]
    total_supply: float
    virtual_price: float
    admin_fee: float
    fee: float
    amplification: int
    timestamp: int

@dataclass
class RebalanceSignal:
    """重新平衡信号"""
    action: str  # 'buy', 'sell', 'hold'
    token: str
    amount: float
    confidence: float
    expected_profit: float
    risk_score: float

class CurvePoolPredictor(nn.Module):
    """Curve池状态预测模型"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 128, num_layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.dropout = nn.Dropout(0.2)
        
        # 多任务预测头
        self.pool_balance_head = nn.Linear(hidden_dim, 3)  # 3个代币的余额比例
        self.apy_head = nn.Linear(hidden_dim, 1)  # APY预测
        self.price_deviation_head = nn.Linear(hidden_dim, 3)  # 价格偏离预测
        self.volume_head = nn.Linear(hidden_dim, 1)  # 交易量预测
        
    def forward(self, x):
        lstm_out, (hidden, cell) = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]  # 取最后一个时间步
        last_hidden = self.dropout(last_hidden)
        
        predictions = {
            'pool_balance': torch.softmax(self.pool_balance_head(last_hidden), dim=-1),
            'apy': torch.sigmoid(self.apy_head(last_hidden)) * 0.2,  # 0-20% APY
            'price_deviation': torch.tanh(self.price_deviation_head(last_hidden)) * 0.01,  # ±1%
            'volume': torch.relu(self.volume_head(last_hidden))
        }
        
        return predictions

class CurveDataCollector:
    """Curve协议数据收集器 (向后兼容版本)"""
    
    def __init__(self, web3_provider: Optional[str] = None):
        if WEB3_AVAILABLE and web3_provider:
            self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        else:
            self.w3 = None
        self.curve_api_base = "https://api.curve.fi/api"
        
        # 导入真实数据收集器
        try:
            from real_data_collector import CurveRealDataCollector
            self.real_collector = CurveRealDataCollector(web3_provider)
            self.use_real_data = True
            print("✅ 使用真实Curve数据")
        except ImportError:
            self.real_collector = None
            self.use_real_data = False
            print("⚠️  真实数据收集器不可用，使用模拟数据")
        
    def get_pool_info(self, pool_address: str) -> Optional[CurvePoolState]:
        """获取池子信息"""
        # 这里应该调用Curve的API或直接与合约交互
        # 简化示例
        try:
            url = f"{self.curve_api_base}/getPools"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                pools_data = response.json()
                # 解析特定池子数据
                for pool in pools_data.get('data', {}).get('poolData', []):
                    if pool.get('address', '').lower() == pool_address.lower():
                        return CurvePoolState(
                            pool_address=pool['address'],
                            tokens=[token['symbol'] for token in pool['coins']],
                            balances=[float(token['poolBalance']) for token in pool['coins']],
                            total_supply=float(pool['totalSupply']),
                            virtual_price=float(pool['virtualPrice']),
                            admin_fee=float(pool['adminFee']),
                            fee=float(pool['fee']),
                            amplification=int(pool['amplificationCoefficient']),
                            timestamp=int(time.time())
                        )
        except Exception as e:
            print(f"Error fetching pool info: {e}")
        
        return None
    
    def get_historical_data(self, pool_address: str, days: int = 30) -> pd.DataFrame:
        """获取历史数据"""
        
        # 如果有真实数据收集器，优先使用真实数据
        if self.use_real_data and self.real_collector:
            try:
                # 根据地址确定池子名称
                pool_name = self._get_pool_name_from_address(pool_address)
                if pool_name:
                    print(f"📊 获取 {pool_name} 真实历史数据...")
                    df = self.real_collector.get_historical_data(pool_name, days)
                    
                    if not df.empty:
                        print(f"✅ 获取到 {len(df)} 条真实历史记录")
                        return df
                    else:
                        print("⚠️  真实数据为空，fallback到模拟数据")
                else:
                    print("⚠️  未知池子地址，使用模拟数据")
            except Exception as e:
                print(f"⚠️  获取真实数据失败: {e}，使用模拟数据")
        
        # Fallback到模拟数据
        print("📊 生成模拟历史数据...")
        dates = pd.date_range(end=pd.Timestamp.now(), periods=days*24, freq='H')
        
        # 模拟数据
        data = {
            'timestamp': dates,
            'usdc_balance': np.random.normal(1000000, 50000, len(dates)),
            'usdt_balance': np.random.normal(1000000, 50000, len(dates)),
            'dai_balance': np.random.normal(1000000, 50000, len(dates)),
            'virtual_price': np.random.normal(1.0, 0.001, len(dates)),
            'volume_24h': np.random.exponential(100000, len(dates)),
            'apy': np.random.normal(0.05, 0.01, len(dates)),
        }
        
        return pd.DataFrame(data)
    
    def _get_pool_name_from_address(self, address: str) -> Optional[str]:
        """根据地址获取池子名称"""
        address_lower = address.lower()
        pool_map = {
            '0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7': '3pool',
            '0xd632f22692fac7611d2aa1c0d552930d43caed3b': 'frax',
            '0x5a6a4d54456819c6cd2fe4de20b59f4f5f3f9b2d': 'mim',
            '0xed279fdd11ca84beef15af5d39bb4d4bee23f0ca': 'lusd'
        }
        return pool_map.get(address_lower)

class CurveRebalancer:
    """Curve智能重新平衡器"""
    
    def __init__(self, model: CurvePoolPredictor, data_collector: CurveDataCollector):
        self.model = model
        self.data_collector = data_collector
        self.min_profit_threshold = 0.001  # 0.1%最小利润阈值
        self.max_risk_score = 0.7  # 最大风险评分
        
    def calculate_imbalance_score(self, predicted_balances: np.ndarray, 
                                 target_balances: np.ndarray) -> float:
        """计算不平衡分数"""
        return np.sum(np.abs(predicted_balances - target_balances))
    
    def calculate_arbitrage_opportunity(self, pool_state: Optional[CurvePoolState], 
                                      predictions: Dict) -> float:
        """计算套利机会"""
        # 简化的套利机会计算
        price_deviations = predictions['price_deviation'].detach().numpy()
        max_deviation = np.max(np.abs(price_deviations))
        
        # 如果价格偏离超过阈值，可能有套利机会
        if max_deviation > 0.005:  # 0.5%
            return max_deviation * 1000  # 转换为盈利估算
        return 0
    
    def generate_rebalance_signal(self, pool_address: str, 
                                lookback_hours: int = 24) -> RebalanceSignal:
        """生成重新平衡信号"""
        
        # 获取历史数据
        historical_data = self.data_collector.get_historical_data(pool_address)
        
        # 准备输入数据
        features = ['usdc_balance', 'usdt_balance', 'dai_balance', 'virtual_price', 'volume_24h']
        X = historical_data[features].values[-lookback_hours:]
        X = torch.FloatTensor(X).unsqueeze(0)  # [1, seq_len, features]
        
        # 模型预测
        self.model.eval()
        with torch.no_grad():
            predictions = self.model(X)
        
        # 分析预测结果
        predicted_balances = predictions['pool_balance'].squeeze().numpy()
        target_balances = np.array([0.333, 0.333, 0.334])  # 理想平衡
        
        imbalance_score = self.calculate_imbalance_score(predicted_balances, target_balances)
        arbitrage_value = self.calculate_arbitrage_opportunity(None, predictions)
        
        # 决策逻辑
        if imbalance_score > 0.05:  # 5%以上的不平衡
            # 找出最不平衡的代币
            deviations = predicted_balances - target_balances
            max_deviation_idx = np.argmax(np.abs(deviations))
            token_names = ['USDC', 'USDT', 'DAI']
            
            if deviations[max_deviation_idx] > 0:
                action = 'sell'
                amount = abs(deviations[max_deviation_idx]) * 1000000  # 转换为实际金额
            else:
                action = 'buy'
                amount = abs(deviations[max_deviation_idx]) * 1000000
            
            return RebalanceSignal(
                action=action,
                token=token_names[max_deviation_idx],
                amount=amount,
                confidence=min(imbalance_score * 2, 1.0),
                expected_profit=arbitrage_value,
                risk_score=imbalance_score
            )
        
        return RebalanceSignal(
            action='hold',
            token='',
            amount=0,
            confidence=0.5,
            expected_profit=0,
            risk_score=0
        )
    
    def execute_rebalance(self, signal: RebalanceSignal) -> bool:
        """执行重新平衡操作"""
        if signal.action == 'hold':
            print("No rebalancing needed")
            return True
            
        if signal.expected_profit < self.min_profit_threshold:
            print(f"Expected profit {signal.expected_profit:.4f} below threshold")
            return False
            
        if signal.risk_score > self.max_risk_score:
            print(f"Risk score {signal.risk_score:.4f} too high")
            return False
        
        print(f"Executing {signal.action} {signal.amount:.2f} {signal.token}")
        print(f"Expected profit: {signal.expected_profit:.4f}")
        print(f"Confidence: {signal.confidence:.4f}")
        
        # 这里应该实际执行交易
        # 简化示例
        return True

# 使用示例
if __name__ == "__main__":
    # 初始化组件
    model = CurvePoolPredictor(input_dim=5)
    data_collector = CurveDataCollector()
    rebalancer = CurveRebalancer(model, data_collector)
    
    # 3Pool地址 (示例)
    pool_address = "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"
    
    # 生成重新平衡信号
    signal = rebalancer.generate_rebalance_signal(pool_address)
    
    # 执行重新平衡
    success = rebalancer.execute_rebalance(signal)
    
    if success:
        print("Rebalancing completed successfully")
    else:
        print("Rebalancing failed or skipped") 