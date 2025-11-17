# 数据源配置指南

## 概述

系统支持多种数据源适配器，可以通过简单的配置切换。

## 可用数据源

### 1. **yfinance** (推荐)
- **稳定性**: ⭐⭐⭐⭐⭐
- **数据覆盖**: A股、港股、美股
- **费用**: 完全免费
- **优点**: 基于Yahoo Finance，全球服务，稳定可靠
- **缺点**: A股数据相对较少，不支持股票搜索

### 2. **akshare**
- **稳定性**: ⭐⭐
- **数据覆盖**: A股、港股
- **费用**: 完全免费
- **优点**: 中文数据全面，支持股票搜索
- **缺点**: 服务不稳定，经常连接失败

## 配置方法

### 方法1: 修改 docker-compose.yml（推荐）

编辑 `docker-compose.yml` 文件，找到backend服务的环境变量：

```yaml
backend:
  environment:
    # 修改这一行，选择数据源
    - DATA_SOURCE=yfinance  # 可选值: 'yfinance' 或 'akshare'
```

然后重启服务：
```bash
docker-compose restart backend
```

### 方法2: 设置环境变量

```bash
export DATA_SOURCE=yfinance
docker-compose up -d
```

## 股票代码格式

不同数据源对股票代码的格式要求略有不同，但系统会自动处理转换：

### A股
- **输入格式**: `600519`, `600519.SH`, `000001.SZ` 均可
- **yfinance格式**: 自动转换为 `600519.SS`, `000001.SZ`
- **akshare格式**: 自动转换为 `600519`, `000001`

### 港股
- **输入格式**: `00700.HK`, `01810.HK` 均可
- **yfinance格式**: 自动转换为 `0700.HK`, `1810.HK` (去除前导0)
- **akshare格式**: 自动转换为 `00700`, `01810`

## 验证配置

重启后，检查日志确认使用的数据源：

```bash
docker-compose logs backend | grep -i "adapter"
```

应该看到类似输出：
```
Registered data adapter: akshare -> AkShareAdapter
Registered data adapter: yfinance -> YFinanceAdapter
```

## 故障排除

### Q: 切换数据源后仍然报错？
A: 确保重启了backend服务：
```bash
docker-compose restart backend
```

### Q: yfinance获取不到某只A股的数据？
A: 某些小盘股可能在Yahoo Finance没有数据，尝试切换回akshare

### Q: 如何添加新的数据源？
A:
1. 在 `backend/app/adapters/` 目录创建新的适配器类
2. 继承 `BaseDataAdapter` 并实现所有抽象方法
3. 在 `factory.py` 中注册新适配器
4. 在配置中使用新适配器名称

## 示例：添加自定义适配器

```python
# backend/app/adapters/custom_adapter.py
from .base import BaseDataAdapter
import pandas as pd

class CustomAdapter(BaseDataAdapter):
    @property
    def name(self) -> str:
        return "Custom"

    def get_stock_data(self, symbol, start_date, end_date, adjust='qfq'):
        # 实现数据获取逻辑
        pass

    def search_stock(self, keyword):
        # 实现搜索逻辑
        pass

    def get_stock_info(self, symbol):
        # 实现信息获取逻辑
        pass
```

```python
# backend/app/adapters/factory.py
# 在 _register_builtin_adapters() 中添加：
from .custom_adapter import CustomAdapter
DataAdapterFactory.register('custom', CustomAdapter)
```

然后在docker-compose.yml中设置：
```yaml
- DATA_SOURCE=custom
```

## 最佳实践

1. **生产环境推荐使用 yfinance** - 更稳定可靠
2. **开发/测试可以用 akshare** - 数据更全面
3. **定期监控数据源可用性** - 设置告警机制
4. **考虑实现降级策略** - 主数据源失败时自动切换备用
