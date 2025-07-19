# Curve智能重新平衡系统

基于量化机器学习的Curve协议智能资产重新平衡系统。

## 项目概述

本项目实现了一个智能的Curve协议资产重新平衡系统，使用深度学习模型预测池子状态，并自动执行优化的重新平衡策略。

### 主要功能

1. **智能预测**: 使用LSTM模型预测池子余额比例、APY、价格偏离等关键指标
2. **风险评估**: 评估交易风险并计算预期收益
3. **自动执行**: 可选的自动交易执行功能
4. **实时监控**: 持续监控池子状态并发出警报

## 模型预测的关键指标

### 1. 池子余额比例 (Pool Balance)
- 预测USDC、USDT、DAI在池中的相对分配比例
- 理想平衡: 33.3% / 33.3% / 33.4%
- 用于识别不平衡机会

### 2. APY收益率 (Annual Percentage Yield)
- 预测池子的年化收益率
- 范围: 0% - 20%
- 基于历史交易量和流动性

### 3. 价格偏离 (Price Deviation)
- 预测各稳定币偏离$1的幅度
- 范围: ±1%
- 用于套利机会识别

### 4. 交易量 (Volume)
- 预测24小时交易量
- 影响收益率和滑点

## 安装和设置

### 1. 安装依赖

```bash
cd Quantum_curve_predict
pip install -r requirements.txt
```

### 2. 训练模型

```bash
# 使用默认参数训练
python train_curve_model.py

# 自定义参数训练
python train_curve_model.py --epochs 100 --batch_size 128 --hidden_dim 256
```

### 3. 运行预测

```bash
# 单次预测 (安全模式)
python run_curve_rebalancer.py --mode single --dry_run

# 持续监控模式
python run_curve_rebalancer.py --mode monitor --interval 15

# 指定特定池子
python run_curve_rebalancer.py --pool_address 0x... --lookback_hours 48
```

### 4. 🆕 获取真实数据 

```bash
# 设置API密钥 (推荐)
export INFURA_API_KEY="your_infura_key"
export ALCHEMY_API_KEY="your_alchemy_key"

# 测试真实数据获取
python demo_real_data.py

# 🆕 测试CSV功能
python example_csv_usage.py

# 🆓 测试免费历史数据获取
python free_historical_data.py

# 检查配置状态
python config.py

# 🏊 扩展更多池子支持
python extend_pools.py
```

## 使用方法

### 基本预测

```bash
# 对3Pool进行单次预测
python run_curve_rebalancer.py --mode single
```

### 实时监控

```bash
# 每15分钟检查一次池子状态
python run_curve_rebalancer.py --mode monitor --interval 15
```

### 高级配置

```bash
# 使用真实Web3节点
python run_curve_rebalancer.py \
    --web3_provider https://eth-mainnet.alchemyapi.io/v2/YOUR-API-KEY \
    --pool_address 0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7 \
    --lookback_hours 24
```

## 输出示例

```
=== 配置信息 ===
Pool Address: 0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7
Model Path: best_curve_model.pth
Web3 Provider: None (使用模拟数据)
Mode: single
Execute: False

=== Curve智能重新平衡 - 单次预测模式 ===
Loading model from best_curve_model.pth...
Model loaded successfully!
  - Epoch: 49
  - Validation Loss: 0.001234

Target Pool: 0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7
Lookback Hours: 24

--- 预测结果 ---
Action: sell
Token: USDC
Amount: $45,230.00
Confidence: 0.832
Expected Profit: 0.008500
Risk Score: 0.076

🔍 仅预测模式，未执行实际交易
✅ 程序执行完成
```

## 文件结构

```
Quantum_curve_predict/
├── curve_rebalancer.py      # 核心重新平衡逻辑
├── train_curve_model.py     # 模型训练脚本
├── run_curve_rebalancer.py  # 主运行脚本
├── real_data_collector.py   # 真实数据获取模块 🆕
├── data_manager.py         # CSV数据管理器 🆕
├── config.py               # 系统配置管理 🆕
├── demo_real_data.py       # 真实数据演示脚本 🆕
├── example_csv_usage.py    # CSV功能使用示例 🆕
├── free_historical_data.py # 免费历史数据获取 🆕
├── quick_free_demo.py      # 免费数据快速演示 🆕
├── quick_demo.py           # 快速演示脚本
├── requirements.txt        # 依赖列表
├── README.md              # 项目说明
├── REAL_DATA_GUIDE.md     # 真实数据获取指南 🆕
├── DATA_SOURCES.md        # 数据源详细说明 🆕
├── POOL_SUPPORT_ANALYSIS.md # 池子支持分析 🆕
├── extend_pools.py        # 池子扩展示例代码 🆕
├── best_curve_model.pth   # 训练好的模型 (训练后生成)
├── training_curve.png     # 训练曲线图 (训练后生成)
└── trade_history.json     # 交易历史记录 (执行后生成)
```

## 模型架构

### CurvePoolPredictor
- **输入**: 历史池子状态数据 (5维特征)
- **架构**: 多层LSTM + 多任务输出头
- **输出**: 
  - 池子余额比例 (3维)
  - APY预测 (1维)
  - 价格偏离 (3维)
  - 交易量预测 (1维)

### 特征工程
- USDC/USDT/DAI余额
- Virtual Price
- 24小时交易量
- 标准化处理

## 风险管理

### 内置安全机制
1. **最小利润阈值**: 0.1%
2. **最大风险评分**: 0.7
3. **置信度评估**: 只执行高置信度操作
4. **干运行模式**: 安全测试功能

### 建议设置
- 首次使用时请使用 `--dry_run` 模式
- 小额测试后再增加资金规模
- 定期检查和更新模型

## 注意事项

⚠️ **重要提醒**:
- 本系统为实验性质，使用前请充分理解风险
- 强烈建议在测试网络上先行测试
- 实际交易前请仔细审查所有参数
- 不承担任何资金损失责任

## 扩展功能

### 支持的池子类型
- 3Pool (USDC/USDT/DAI)
- 其他稳定币池 (需要调整参数)

### 🌐 真实数据支持 (新功能)
- ✅ **Curve官方API**: 获取最准确的池子数据
- ✅ **The Graph子图**: 丰富的历史数据查询
- ✅ **区块链直读**: 实时精确的链上数据
- ✅ **多数据源备份**: 自动切换确保数据可用性
- ✅ **数据质量验证**: 自动检查数据合理性

### 💾 CSV数据存储 (新功能)
- ✅ **自动CSV导出**: 获取的数据自动保存为CSV格式
- ✅ **目录管理**: 按类型组织数据文件
- ✅ **历史记录**: 保留完整的数据获取历史
- ✅ **数据读取**: 支持从CSV文件训练模型
- ✅ **批量操作**: 一次性处理多个池子数据

### 🆓 免费历史数据 (新功能)
- ✅ **The Graph**: 1000次查询/天，获取30天历史数据
- ✅ **DefiLlama**: 无限制，免费APY历史数据
- ✅ **自建数据库**: 通过定期收集积累历史数据
- ✅ **综合策略**: 多源免费数据自动合并
- ✅ **定时收集**: 设置cron任务长期积累数据

支持的数据类型：
- 实时池子状态 (余额、虚拟价格、APY) → CSV保存
- 历史交易数据 (30天内的每小时数据) → CSV保存
- 多池子数据对比 (3Pool, FRAX, MIM, LUSD等) → 批量CSV导出
- 价格偏离监控 (稳定币脱锚检测) → 自动分析

数据目录结构：
```
curve_data/
├── real_time/        # 实时数据CSV
├── historical/       # 历史数据CSV
└── backups/          # 备份文件
```

### 未来改进
- [ ] 支持更多池子类型 
- [x] ✅ 集成真实价格Feed
- [ ] 优化交易执行策略
- [ ] 添加更多技术指标
- [ ] 实现MEV保护
- [x] ✅ 多数据源整合

## 🚀 快速开始 (真实数据版)

### 方式1: 快速演示 (推荐)
```bash
# 运行完整演示，包括真实数据获取
python demo_real_data.py

# 🆓 或者运行免费历史数据演示
python quick_free_demo.py
```

### 方式2: 设置真实数据
```bash
# 1. 获取免费API密钥
# Infura: https://infura.io/register
# Alchemy: https://alchemy.com/

# 2. 设置环境变量
export INFURA_API_KEY="your_key_here"

# 3. 测试数据获取
python config.py

# 4. 🆕 先获取并保存CSV数据
python example_csv_usage.py

# 5. 🆕 使用CSV数据训练模型
python train_curve_model.py --use-real-data

# 6. 运行预测
python run_curve_rebalancer.py --mode single
```

### 方式3: 🆓 免费历史数据 (无需API密钥)
```bash
# 完全免费获取历史数据
python free_historical_data.py

# 使用免费数据训练模型
python train_curve_model.py --use-real-data --csv-data-dir free_historical_cache
```

### 方式4: 无API密钥使用
```bash
# 系统会自动使用模拟数据
python quick_demo.py
```

## 📚 详细文档

- 📖 [真实数据获取指南](REAL_DATA_GUIDE.md) - 完整的数据获取教程
- 📖 [数据源详解](DATA_SOURCES.md) - 各平台API详细说明
- 🆓 [免费历史数据策略](free_historical_data.py) - 无需付费获取历史数据
- 🏊 [池子支持分析](POOL_SUPPORT_ANALYSIS.md) - 支持池子详情和扩展方案
- 📊 数据源对比和选择建议
- 🔧 API密钥配置和故障排除
- 💡 最佳实践和性能优化

## 技术支持

如有问题请检查:
1. 所有依赖是否正确安装 (`pip install -r requirements.txt`)
2. 模型是否已训练完成 (`python train_curve_model.py`)
3. Web3连接是否正常 (`python config.py`)
4. 池子地址是否正确
5. **🆕 API密钥是否正确设置** (`python demo_real_data.py`)

## 许可证

MIT License - 详见LICENSE文件 