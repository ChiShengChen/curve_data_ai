# Curve 真实数据获取指南

本指南详细介绍如何获取 Curve 协议的真实数据，用于智能重新平衡系统。

## 🌐 数据源概览

我们的系统支持多种数据源，按优先级排序：

| 数据源 | 类型 | 优势 | 限制 |
|--------|------|------|------|
| **Curve API** | REST API | 官方数据，最准确 | 有时不稳定 |
| **The Graph** | GraphQL | 历史数据丰富 | 查询复杂 |
| **区块链直读** | RPC调用 | 实时精确 | 需要节点API |
| **DefiLlama** | REST API | APY数据好 | 更新较慢 |
| **CoinGecko** | REST API | 价格数据 | 非池子特定 |

## 🔑 API 密钥设置

### 1. Web3 节点提供商 (推荐)

获取免费API密钥：

- **Infura**: https://infura.io/register
  ```bash
  export INFURA_API_KEY="your_key_here"
  ```

- **Alchemy**: https://alchemy.com/
  ```bash
  export ALCHEMY_API_KEY="your_key_here"  
  ```

- **QuickNode**: https://quicknode.com/
  ```bash
  export QUICKNODE_API_KEY="your_key_here"
  ```

### 2. 价格数据API (可选)

- **CoinGecko**: https://www.coingecko.com/en/api
  ```bash
  export COINGECKO_API_KEY="your_key_here"
  ```

### 3. 使用 .env 文件 (推荐)

创建 `.env` 文件：
```env
# Web3 提供商 (选择一个)
INFURA_API_KEY=your_infura_key_here
ALCHEMY_API_KEY=your_alchemy_key_here

# 可选
COINGECKO_API_KEY=your_coingecko_key_here
```

## 📊 获取不同类型的数据

### 1. 实时池子数据

```python
from real_data_collector import CurveRealDataCollector

# 初始化收集器
collector = CurveRealDataCollector()

# 获取3Pool实时数据
pool_data = collector.get_real_time_data('3pool')

if pool_data:
    print(f"池子: {pool_data.pool_name}")
    print(f"代币: {pool_data.tokens}")
    print(f"余额: {pool_data.balances}")
    print(f"Virtual Price: {pool_data.virtual_price}")
    print(f"APY: {pool_data.apy:.2%}")
    print(f"24h交易量: ${pool_data.volume_24h:,.0f}")
```

### 2. 历史数据

```python
# 获取过去30天的历史数据
historical_df = collector.get_historical_data('3pool', days=30)

if not historical_df.empty:
    print(f"获取到 {len(historical_df)} 条历史记录")
    print(historical_df.head())
```

### 3. 多池子数据对比

```python
pools = ['3pool', 'frax', 'mim', 'lusd']

for pool in pools:
    data = collector.get_real_time_data(pool)
    if data:
        print(f"{pool}: APY={data.apy:.2%}, Volume=${data.volume_24h:,.0f}")
```

## 🎯 支持的池子

| 池子名称 | 地址 | 代币 | 特点 |
|----------|------|------|------|
| **3pool** | `0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7` | USDC/USDT/DAI | 最大的稳定币池 |
| **frax** | `0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B` | FRAX/USDC | 算法稳定币 |
| **mim** | `0x5a6A4D54456819C6Cd2fE4de20b59F4f5F3f9b2D` | MIM/3CRV | Magic Internet Money |
| **lusd** | `0xEd279fDD11cA84bEef15AF5D39BB4d4bEE23F0cA` | LUSD/3CRV | Liquity USD |

## 📈 数据字段说明

### CurvePoolData 结构

```python
@dataclass
class CurvePoolData:
    pool_address: str      # 池子合约地址
    pool_name: str         # 池子名称
    tokens: List[str]      # 代币符号列表 ['USDC', 'USDT', 'DAI']
    balances: List[float]  # 各代币余额
    rates: List[float]     # 汇率 (通常稳定币为1.0)
    total_supply: float    # LP代币总供应量
    virtual_price: float   # 虚拟价格 (1.0以上表示增值)
    volume_24h: float      # 24小时交易量 (USD)
    fees_24h: float        # 24小时手续费收入
    apy: float            # 年化收益率 (0.05 = 5%)
    timestamp: datetime    # 数据时间戳
```

## 🔍 使用真实数据的步骤

### 1. 安装完整依赖

```bash
cd Quantum_curve_predict
pip install -r requirements.txt
```

### 2. 设置API密钥

```bash
# 方法1: 环境变量
export INFURA_API_KEY="your_key_here"

# 方法2: .env文件
echo "INFURA_API_KEY=your_key_here" > .env
```

### 3. 测试数据获取

```bash
# 运行演示脚本
python demo_real_data.py

# 检查配置状态
python config.py
```

### 4. 训练模型使用真实数据

```bash
# 使用真实数据训练模型
python train_curve_model.py --use-real-data

# 使用真实数据运行预测
python run_curve_rebalancer.py --mode single --use-real-data
```

## 🚀 快速开始示例

```python
#!/usr/bin/env python3
"""
快速开始: 获取3Pool真实数据
"""

from real_data_collector import CurveRealDataCollector

def main():
    # 1. 初始化收集器
    collector = CurveRealDataCollector()
    
    # 2. 获取实时数据
    print("获取3Pool实时数据...")
    pool_data = collector.get_real_time_data('3pool')
    
    if pool_data:
        # 3. 分析数据
        total_balance = sum(pool_data.balances)
        ratios = [b/total_balance for b in pool_data.balances]
        
        print(f"代币分配比例:")
        for token, ratio in zip(pool_data.tokens, ratios):
            print(f"  {token}: {ratio:.1%}")
        
        # 4. 检查不平衡
        ideal_ratio = 1/3
        max_deviation = max(abs(r - ideal_ratio) for r in ratios)
        
        if max_deviation > 0.05:  # 5%偏离
            print(f"⚠️  池子存在不平衡! 最大偏离: {max_deviation:.1%}")
        else:
            print("✅ 池子平衡良好")
    
    # 5. 获取历史趋势
    print("\n获取历史数据...")
    df = collector.get_historical_data('3pool', days=7)
    
    if not df.empty:
        if 'virtual_price' in df.columns:
            price_change = (df['virtual_price'].iloc[-1] / df['virtual_price'].iloc[0] - 1) * 100
            print(f"Virtual Price 7天变化: {price_change:+.4f}%")

if __name__ == "__main__":
    main()
```

## ⚠️ 注意事项

### API 限制
- **Curve API**: 无官方限制说明，建议不超过1次/秒
- **The Graph**: 1000次/天 (免费)，可申请更高限额
- **CoinGecko**: 50次/分钟 (免费)，可购买Pro版本
- **Infura/Alchemy**: 10万次/天 (免费)，付费计划更高

### 数据延迟
- **Curve API**: ~30秒延迟
- **区块链直读**: 实时 (区块确认时间)
- **The Graph**: ~5分钟延迟
- **DefiLlama**: ~1小时延迟

### 错误处理
系统内置多层错误处理：
1. API失败自动切换数据源
2. 数据验证检查异常值
3. 网络错误重试机制
4. 无数据时使用模拟数据兜底

## 📊 数据质量验证

运行数据质量检查：

```python
from demo_real_data import demo_data_quality

# 执行数据质量检查
demo_data_quality()
```

检查项目：
- ✅ 数据完整性 (必填字段)
- ✅ 数值合理性 (APY范围，余额正数等)
- ✅ 时间戳新鲜度
- ✅ 池子平衡度
- ✅ 价格一致性

## 🛠 故障排除

### 常见问题

1. **"无法获取数据"**
   ```bash
   # 检查网络连接
   curl -s "https://api.curve.fi/api/getPools/ethereum/main" | head
   
   # 检查API密钥
   python config.py
   ```

2. **"数据为空"**
   - 检查池子名称拼写
   - 确认池子地址正确
   - 查看是否API暂时不可用

3. **"Web3连接失败"**
   - 确认API密钥正确设置
   - 检查网络防火墙设置
   - 尝试不同的节点提供商

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

collector = CurveRealDataCollector(web3_provider_url="your_url")
```

## 💡 最佳实践

1. **缓存数据**: 避免频繁API调用
2. **错误重试**: 网络不稳定时自动重试
3. **数据验证**: 使用前检查数据合理性
4. **备用方案**: 多数据源备份策略
5. **监控告警**: 设置数据异常告警

## 📞 技术支持

如遇问题：

1. 查看日志输出
2. 运行 `python demo_real_data.py` 诊断
3. 检查 API 密钥配置
4. 确认网络连接正常

---

🎉 现在你可以获取 Curve 的真实数据来优化你的重新平衡策略了！ 