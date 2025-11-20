# AI智能分析功能 - 配置和使用指南

## 功能概述

系统已集成**阿里云通义千问-Plus** AI分析能力，可以为回测结果提供智能点评和优化建议。

### 功能特性
- ✅ 策略表现评估
- ✅ 风险分析
- ✅ 参数优化建议
- ✅ 改进方向指导

---

## 配置步骤

### 1. 获取阿里云API Key

#### 步骤：
1. 访问阿里云DashScope控制台：https://dashscope.console.aliyun.com/
2. 登录/注册阿里云账号
3. 进入"API-KEY管理"页面
4. 点击"创建新的API-KEY"
5. 复制生成的API Key（格式: `sk-xxxxxxxxxxxxxxxx`）

#### 定价参考：
- **通义千问-Plus**: ¥0.004/千tokens
- **免费额度**: 新用户通常有免费试用额度
- **预估成本**: 单次分析约消耗500-800 tokens，成本约¥0.002-0.003

### 2. 配置API Key

#### 方式1: Docker环境变量（推荐）

编辑 `docker-compose.yml`，取消注释并填入API Key:

```yaml
environment:
  # AI分析服务配置（阿里云通义千问）
  - QWEN_API_KEY=sk-your-actual-api-key-here  # 填入你的API Key
  - QWEN_MODEL=qwen-plus
  - QWEN_TIMEOUT=30
  - QWEN_MAX_TOKENS=1000
```

#### 方式2: 环境变量文件

创建 `backend/.env` 文件:

```env
QWEN_API_KEY=sk-your-actual-api-key-here
QWEN_MODEL=qwen-plus
QWEN_TIMEOUT=30
QWEN_MAX_TOKENS=1000
```

### 3. 重启服务

```bash
# 重启后端服务
make restart-backend

# 或者
docker-compose restart backend
```

### 4. 验证配置

测试API是否配置成功:

```bash
python3 test_ai_api.py
```

**成功响应示例**:
```json
{
  "success": true,
  "data": {
    "analysis": "## 策略表现评估\\n您的MACD金叉策略...",
    "tokens_used": 756,
    "model": "qwen-plus",
    "analysis_time": 3.2
  }
}
```

**未配置时的响应**:
```json
{
  "success": false,
  "message": "AI分析服务未配置。请联系管理员配置QWEN_API_KEY。"
}
```

---

## API使用

### 端点信息

```
POST /api/v1/backtest/analyze
Content-Type: application/json
```

### 请求格式

```json
{
  "stock_info": {
    "symbol": "600000",
    "name": "浦发银行",
    "period": "2023-01-01 至 2024-12-31"
  },
  "strategy_info": {
    "name": "MACD金叉策略",
    "description": "当MACD金叉时买入，死叉时卖出"
  },
  "parameters": {
    "initial_capital": 100000,
    "commission_rate": 0.0003,
    "strategy_params": {
      "fast_period": 12,
      "slow_period": 26,
      "signal_period": 9
    }
  },
  "backtest_results": {
    "total_return": 0.25,
    "win_rate": 0.55,
    "max_drawdown": 0.18,
    "profit_factor": 1.8,
    "total_trades": 24,
    "winning_trades": 13,
    "losing_trades": 11
  }
}
```

### 响应格式

```json
{
  "success": true,
  "data": {
    "analysis": "Markdown格式的分析文本",
    "tokens_used": 756,
    "model": "qwen-plus",
    "analysis_time": 3.2
  }
}
```

---

## 前端集成（待实现）

### 需要添加的组件

1. **AI分析按钮** - 在回测结果页面
2. **分析结果展示** - Markdown渲染组件
3. **加载状态** - 分析进行中的提示

### 实现示例

```typescript
// 调用AI分析
const analyzeBacktest = async () => {
  const response = await fetch('/api/v1/backtest/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(backtestData)
  });

  const result = await response.json();
  if (result.success) {
    setAnalysis(result.data.analysis);
  }
};
```

---

## 配置选项说明

### 环境变量

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `QWEN_API_KEY` | 阿里云API密钥 | - | ✅ 是 |
| `QWEN_MODEL` | 模型名称 | `qwen-plus` | ❌ 否 |
| `QWEN_TIMEOUT` | 超时时间（秒） | `30` | ❌ 否 |
| `QWEN_MAX_TOKENS` | 最大token数 | `1000` | ❌ 否 |

### 可选模型

| 模型 | 特点 | 定价 |
|------|------|------|
| `qwen-plus` | 推荐，性价比高 | ¥0.004/千tokens |
| `qwen-turbo` | 更快，成本更低 | ¥0.002/千tokens |
| `qwen-max` | 最强能力 | ¥0.02/千tokens |

---

## 成本控制建议

### 1. 预估使用量

- 单次分析: 500-800 tokens
- 单次成本: ¥0.002-0.003
- 月100次使用: 约¥0.2-0.3

### 2. 控制措施（待实现）

- ✅ 设置超时时间（已实现）
- ⏳ 用户每日调用次数限制
- ⏳ 全局每日调用上限
- ⏳ 缓存相同回测结果
- ⏳ 成本监控告警

---

## 常见问题

### Q: API Key在哪里获取？
**A:** https://dashscope.console.aliyun.com/apiKey

### Q: 如何确认配置成功？
**A:** 运行 `python3 test_ai_api.py`，看到 `"success": true` 即为成功

### Q: 调用失败怎么办？
**A:** 检查：
1. API Key 是否正确
2. 账户余额是否充足
3. 网络是否正常
4. 查看后端日志: `make logs-backend`

### Q: 如何更换模型？
**A:** 修改 `QWEN_MODEL` 环境变量为 `qwen-turbo` 或 `qwen-max`

### Q: 成本太高怎么办？
**A:**
- 使用 `qwen-turbo` 模型（成本减半）
- 减少 `QWEN_MAX_TOKENS`（如设为500）
- 实现缓存机制避免重复分析

---

## 安全提示

⚠️ **重要**:
- 不要将API Key提交到Git仓库
- 不要在前端代码中暴露API Key
- 定期轮换API Key
- 监控API调用量和成本

---

## 技术架构

```
用户 → 前端按钮 → POST /api/v1/backtest/analyze
                      ↓
              AIAnalysisService
                      ↓
              阿里云通义千问API
                      ↓
              Markdown格式分析结果
                      ↓
              前端渲染展示
```

---

## 相关资源

- [阿里云DashScope文档](https://help.aliyun.com/zh/dashscope/)
- [通义千问API参考](https://help.aliyun.com/zh/dashscope/developer-reference/api-details)
- [通义千问定价](https://help.aliyun.com/zh/dashscope/product-overview/billing-overview)

---

**最后更新**: 2025-11-20
**功能状态**: ✅ 后端已完成，⏳ 前端待实现
