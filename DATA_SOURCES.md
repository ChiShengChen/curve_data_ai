# Curve 链上数据来源详解

本系统使用多个平台的API来获取Curve协议的链上数据，以下是详细说明：

## 🌐 主要数据源

### 1. **Curve 官方 API** (主要数据源)
- **平台**: Curve Finance 官方
- **端点**: `https://api.curve.fi`
- **具体API**: `https://api.curve.fi/api/getPools/ethereum/main`
- **数据类型**: 
  - 池子基本信息 (地址、名称、代币)
  - 实时余额数据
  - Virtual Price
  - 24小时交易量
  - 手续费数据
  - APY (年化收益率)
- **更新频率**: ~30秒
- **限制**: 无官方限制说明
- **优势**: 最官方、最准确的数据

```python
# 示例调用
url = "https://api.curve.fi/api/getPools/ethereum/main"
response = requests.get(url)
pools_data = response.json()
```

### 2. **The Graph 子图** (历史数据)
- **平台**: The Graph Protocol
- **端点**: `https://api.thegraph.com/subgraphs/name/messari/curve-finance-ethereum`
- **查询方式**: GraphQL
- **数据类型**:
  - 历史池子快照
  - 每日/每小时数据
  - 交易历史
  - TVL变化
- **历史深度**: 最多30天
- **限制**: 1000次查询/天 (免费版)
- **优势**: 丰富的历史数据，支持复杂查询

```graphql
# GraphQL查询示例
{
  pool(id: "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7") {
    dailyPoolSnapshots(first: 7, orderBy: timestamp, orderDirection: desc) {
      timestamp
      totalValueLockedUSD
      dailyVolumeUSD
      virtualPrice
    }
  }
}
```

### 3. **区块链直读** (实时精确数据)
- **平台**: 以太坊节点提供商
- **支持的提供商**:
  - **Infura**: `https://mainnet.infura.io/v3/{API_KEY}`
  - **Alchemy**: `https://eth-mainnet.g.alchemy.com/v2/{API_KEY}`
  - **QuickNode**: 等其他节点服务
- **访问方式**: Web3.py 通过 JSON-RPC
- **数据类型**:
  - 合约状态 (余额、Virtual Price)
  - 实时区块数据
  - 事件日志
- **优势**: 最实时、最准确
- **劣势**: 需要API密钥，调用成本较高

```python
# Web3调用示例
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR-API-KEY"))
contract = w3.eth.contract(address=pool_address, abi=pool_abi)
virtual_price = contract.functions.get_virtual_price().call()
```

### 4. **DefiLlama** (收益率数据)
- **平台**: DefiLlama 
- **端点**: `https://yields.llama.fi`
- **具体API**: `https://yields.llama.fi/pools`
- **数据类型**:
  - APY数据
  - TVL信息
  - 协议统计
- **更新频率**: ~1小时
- **限制**: 无严格限制
- **优势**: 专业的DeFi收益数据聚合

```python
# DefiLlama API调用
url = "https://yields.llama.fi/pools"
response = requests.get(url)
apy_data = response.json()
```

### 5. **CoinGecko** (价格数据)
- **平台**: CoinGecko
- **端点**: `https://api.coingecko.com/api/v3`
- **具体API**: `https://api.coingecko.com/api/v3/simple/price`
- **数据类型**:
  - 代币实时价格
  - 市场数据
  - 历史价格
- **限制**: 50次/分钟 (免费)，可购买Pro版本
- **优势**: 最全面的代币价格数据

```python
# CoinGecko价格查询
url = "https://api.coingecko.com/api/v3/simple/price"
params = {'ids': 'usd-coin,tether,dai', 'vs_currencies': 'usd'}
response = requests.get(url, params=params)
```

## 🔄 数据获取策略

### 优先级顺序
1. **Curve官方API** (最高优先级) → 实时池子数据
2. **The Graph** → 历史数据补充
3. **区块链直读** → 当API不可用时的备选
4. **DefiLlama** → APY数据补强
5. **CoinGecko** → 价格数据支持

### 自动切换机制
```python
def get_real_time_data(self, pool_name: str):
    # 1. 尝试Curve官方API
    data = self.get_curve_api_data(pool_name)
    if data:
        return data
    
    # 2. Fallback到区块链直读
    if self.w3:
        data = self.get_onchain_data(pool_address)
        if data:
            return data
    
    # 3. 最后使用模拟数据
    return self.generate_mock_data(pool_name)
```

## 📊 数据质量保证

### 数据验证
- **完整性检查**: 必填字段验证
- **合理性检查**: 数值范围验证 
- **一致性检查**: 多源数据对比
- **时效性检查**: 时间戳新鲜度

### 错误处理
- **网络超时**: 自动重试 + 备用源
- **API限制**: 智能频率控制
- **数据异常**: 异常值过滤
- **服务不可用**: 优雅降级

## 🔑 API 密钥配置

### 免费获取地址
| 服务商 | 免费额度 | 获取链接 | 月费用(付费版) |
|--------|----------|----------|---------------|
| **Infura** | 10万请求/天 | https://infura.io/register | $50起 |
| **Alchemy** | 3亿CU/月 | https://alchemy.com/ | $199起 |
| **CoinGecko** | 50次/分钟 | https://www.coingecko.com/en/api | $129起 |
| **The Graph** | 1000次/天 | https://thegraph.com/ | 按查询量 |

### 配置方法
```bash
# 环境变量方式
export INFURA_API_KEY="your_infura_key"
export ALCHEMY_API_KEY="your_alchemy_key"
export COINGECKO_API_KEY="your_coingecko_key"

# 或创建 .env 文件
echo "INFURA_API_KEY=your_key" > .env
```

## 📈 数据更新频率

| 数据源 | 实时数据 | 历史数据 | 典型延迟 |
|--------|----------|----------|----------|
| Curve API | ✅ | ❌ | 30秒 |
| The Graph | ❌ | ✅ | 5分钟 |
| 区块链直读 | ✅ | ✅ | 实时 |
| DefiLlama | ✅ | ✅ | 1小时 |
| CoinGecko | ✅ | ✅ | 2分钟 |

## 🛡️ 数据安全性

### API密钥保护
- 环境变量存储
- 不写入代码/日志
- 定期轮换密钥

### 数据备份
- 本地CSV备份
- 多源数据对比
- 异常数据告警

## 💡 最佳实践

1. **多源验证**: 重要决策使用多个数据源确认
2. **缓存策略**: 避免频繁API调用
3. **优雅降级**: API不可用时使用历史数据
4. **监控告警**: 设置数据异常告警
5. **成本控制**: 合理分配API调用额度

## 🔗 相关链接

- [Curve官方文档](https://curve.readthedocs.io/)
- [The Graph文档](https://thegraph.com/docs/)
- [Web3.py文档](https://web3py.readthedocs.io/)
- [Infura文档](https://docs.infura.io/)
- [Alchemy文档](https://docs.alchemy.com/)

---

💡 **提示**: 系统会自动选择最佳的数据源组合，你只需要设置好API密钥即可享受高质量的链上数据！ 