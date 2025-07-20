# 🚀 Curve池子批量数据获取系统 - 扩展版

> **全面支持37+主要Curve池子的批量历史数据获取**

## ✨ 新功能概览

### 🎯 扩展特性
- **37+池子支持**: 覆盖所有主要Curve池子 
- **智能分级**: 按优先级(1-5)和类型分类管理
- **批量获取**: 高效的并发数据获取
- **多维筛选**: 按优先级、类型、自定义条件筛选  
- **数据分析**: 内置统计分析和报告生成
- **Excel导出**: 带汇总表的Excel文件导出
- **缓存优化**: 智能缓存避免重复请求

### 🏊‍♀️ 支持的池子类型

| 类型 | 数量 | 描述 | 示例 |
|------|------|------|------|
| `stable` | 1个 | 主要稳定币池 | 3pool |
| `metapool` | 13个 | Meta池子 | FRAX, LUSD, MIM |  
| `eth_pool` | 4个 | ETH相关池子 | stETH, rETH |
| `btc_pool` | 3个 | BTC相关池子 | renBTC, sBTC |
| `crypto` | 2个 | 加密资产池 | tricrypto |
| `lending` | 4个 | 借贷池子 | AAVE, Compound |
| `btc_metapool` | 4个 | BTC Meta池 | bBTC, oBTC |
| `yield` | 3个 | 收益池子 | Y池, BUSD |
| `international` | 1个 | 国际化币种 | EURS |
| `synthetic` | 1个 | 合成资产 | LINK |
| `stable_4pool` | 1个 | 4币种稳定池 | sUSD |

### 📊 优先级分级

| 优先级 | 标识 | 数量 | 描述 |
|--------|------|------|------|
| 1 | 🏆 最高 | 1个 | 最重要池子 (3pool) |
| 2 | ⭐ 高 | 5个 | 主要交易池 |
| 3 | 📈 中 | 6个 | 重要流动性池 |
| 4 | 📊 低 | 16个 | 专业/小众池 |
| 5 | 🔽 最低 | 9个 | 实验/已废弃池 |

## 🎯 快速开始

### 1. 高优先级池子快速获取

```python
from free_historical_data import FreeHistoricalDataManager

# 创建管理器
manager = FreeHistoricalDataManager()

# 获取高优先级池子数据
batch_data = manager.get_high_priority_pools_data(days=7)

# 查看结果
for pool_name, df in batch_data.items():
    if not df.empty:
        print(f"{pool_name}: {len(df)} 条记录")
```

### 2. 按类型获取数据

```python
# 获取所有ETH相关池子
eth_data = manager.get_pools_by_type_data('eth_pool', days=7)

# 获取所有稳定币池子  
stable_data = manager.get_stable_pools_data(days=7)

# 获取所有BTC相关池子
btc_data = manager.get_pools_by_type_data('btc_pool', days=7)
```

### 3. 自定义筛选

```python
from free_historical_data import get_pools_by_priority

# 获取优先级1-3的稳定币池
selected_pools = get_pools_by_priority(
    min_priority=1,
    max_priority=3, 
    pool_types=['stable', 'metapool']
)

# 批量获取数据
custom_data = manager.get_batch_historical_data(selected_pools, days=7)
```

### 4. 数据分析和导出

```python
# 获取主要池子数据
main_data = manager.get_all_main_pools_data(days=7)

# 生成分析报告
analysis = manager.analyze_batch_data(main_data)

# 导出到Excel
excel_path = manager.export_batch_data_to_excel(
    main_data, 
    "curve_pools_analysis.xlsx"
)
```

## 📚 完整API参考

### 核心获取方法

```python
# 按优先级获取
manager.get_high_priority_pools_data(days=7)      # 优先级1-2
manager.get_all_main_pools_data(days=7)           # 优先级1-3  
manager.get_all_pools_data(days=7)                # 所有池子

# 按类型获取
manager.get_stable_pools_data(days=7)             # 稳定币池
manager.get_pools_by_type_data('eth_pool', days=7) # 特定类型

# 批量获取 (核心方法)
manager.get_batch_historical_data(
    pools_dict,                    # 池子字典
    days=7,                        # 获取天数
    max_concurrent=3,              # 最大并发数
    delay_between_batches=2        # 批次间延迟(秒)
)
```

### 筛选工具函数

```python
from free_historical_data import get_pools_by_priority

# 灵活筛选
get_pools_by_priority(
    min_priority=1,                # 最小优先级
    max_priority=5,                # 最大优先级  
    pool_types=['stable', 'metapool']  # 池子类型列表
)

# 快捷筛选
get_high_priority_pools()          # 优先级1-2
get_all_main_pools()               # 优先级1-3
get_stable_pools()                 # 所有稳定币池
```

### 数据分析方法

```python
# 生成分析报告
analysis_df = manager.analyze_batch_data(batch_data)

# Excel导出
excel_path = manager.export_batch_data_to_excel(
    batch_data,
    filename="custom_name.xlsx"    # 可选自定义文件名
)
```

## 🖥️ 命令行工具

### 信息查看

```bash
# 查看所有可用池子信息
python free_historical_data.py info

# 演示批量获取功能
python free_historical_data.py batch

# 运行完整演示
python free_historical_data.py all
```

### 测试脚本

```bash
# 运行全面测试
python test_batch_pools.py

# 运行使用示例
python example_usage.py           # 运行所有示例
python example_usage.py 1         # 快速开始示例
python example_usage.py production # 生产环境示例
```

## 📈 使用场景

### 🎯 推荐获取策略

| 场景 | 推荐方法 | 池子数量 | 用途 |
|------|----------|----------|------|
| 快速测试 | `get_high_priority_pools_data()` | 6个 | 验证功能 |
| 日常分析 | `get_all_main_pools_data()` | 12个 | 常规分析 |
| 专业研究 | `get_all_pools_data()` | 28个 | 全面分析 |
| 稳定币分析 | `get_stable_pools_data()` | 15个 | 稳定币研究 |
| ETH生态 | `get_pools_by_type_data('eth_pool')` | 4个 | ETH相关分析 |

### 💡 最佳实践

1. **API限制友好**
   ```python
   # 合理设置并发和延迟
   batch_data = manager.get_batch_historical_data(
       pools_dict, 
       max_concurrent=2,           # 不要超过3
       delay_between_batches=3     # 建议3秒以上
   )
   ```

2. **缓存利用**
   ```python
   # 相同参数会自动使用缓存，避免重复请求
   data1 = manager.get_high_priority_pools_data(days=7)  # 请求API
   data2 = manager.get_high_priority_pools_data(days=7)  # 使用缓存
   ```

3. **错误处理**
   ```python
   try:
       batch_data = manager.get_all_pools_data(days=7)
       successful = sum(1 for df in batch_data.values() if not df.empty)
       print(f"成功获取: {successful}/{len(batch_data)} 个池子")
   except Exception as e:
       print(f"批量获取失败: {e}")
   ```

## 🔧 配置选项

### 修改默认设置

```python
# 在 free_historical_data.py 中修改
CURRENT_DAYS_SETTING = QUICK_TEST_DAYS    # 7天 (推荐)
CURRENT_DAYS_SETTING = MEDIUM_RANGE_DAYS  # 90天
CURRENT_DAYS_SETTING = FULL_YEAR_DAYS     # 365天

# API配置
ENABLE_CURVE_API = True          # Curve官方API
ENABLE_DEFILLAMA = True          # DeFiLlama API
ENABLE_SSL_VERIFICATION = False  # SSL验证 (建议False)
```

### 池子配置

所有池子配置在 `AVAILABLE_POOLS` 字典中，包含:
- `address`: 池子合约地址  
- `name`: 显示名称
- `tokens`: 包含的代币列表
- `type`: 池子类型  
- `priority`: 优先级 (1-5)

## 📊 输出格式

### 数据结构

每个池子的数据包含以下列:
- `timestamp`: 时间戳
- `virtual_price`: 虚拟价格 (重要指标)
- `volume_24h`: 24小时交易量
- `pool_name`: 池子名称  
- `pool_type`: 池子类型
- `priority`: 优先级
- `source`: 数据来源

### Excel文件结构

导出的Excel文件包含:
1. **Summary工作表**: 所有池子的汇总信息
2. **各池子工作表**: 每个池子的详细数据
3. **统计信息**: 数据质量、来源分布等

## 🎉 总结

现在你可以轻松获取**37+主要Curve池子**的历史数据！

### ✅ 主要优势
- **覆盖全面**: 支持所有主要Curve池子
- **智能分级**: 按重要性和类型组织  
- **高效批量**: 并发获取，智能缓存
- **灵活筛选**: 多维度自定义选择
- **完善分析**: 内置统计和可视化  
- **易于使用**: 丰富的API和示例

### 🚀 开始使用

```bash
# 1. 查看所有池子
python free_historical_data.py info

# 2. 快速测试
python test_batch_pools.py  

# 3. 学习示例
python example_usage.py

# 4. 开始你的分析！
python -c "
from free_historical_data import FreeHistoricalDataManager
manager = FreeHistoricalDataManager()
data = manager.get_high_priority_pools_data()
print('获取完成! 池子数量:', len(data))
"
```

**Happy Curve Data Analysis! 🎯📈** 