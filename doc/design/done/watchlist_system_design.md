# 自选股管理系统 - 详细设计文档

**版本**: v1.0
**创建时间**: 2025-11-19
**状态**: 设计中
**关联文档**:
- Backlog: `doc/backlog/自选股管理系统.md` (BL-015)
- 依赖: `doc/backlog/用户账户系统.md` (BL-003)

---

## 目录

1. [概述](#1-概述)
2. [背景与动机](#2-背景与动机)
3. [总体架构设计](#3-总体架构设计)
4. [数据模型设计](#4-数据模型设计)
5. [API接口设计](#5-api接口设计)
6. [实时行情方案](#6-实时行情方案)
7. [前端设计](#7-前端设计)
8. [安全与权限](#8-安全与权限)
9. [性能优化方案](#9-性能优化方案)
10. [实施计划](#10-实施计划)
11. [测试策略](#11-测试策略)
12. [风险与挑战](#12-风险与挑战)
13. [未来扩展](#13-未来扩展)

---

## 1. 概述

### 1.1 目的

实现完整的自选股管理系统，为散户用户提供股票收藏、分组管理、实时行情监控、快速回测等核心功能，显著提升用户使用体验和系统粘性。

### 1.2 目标

**核心功能（P0）：**
- ✅ 自选股增删改查（CRUD）
- ✅ 分组创建和管理
- ✅ 股票列表展示（基本信息：代码、名称、添加时间）
- ✅ 与回测功能深度集成（快速跳转）
- ✅ 基于用户账户的数据存储（需要登录）

**重要功能（P1）：**
- ✅ 实时行情展示（当前价、涨跌幅）
- ✅ 按分组筛选和排序
- ✅ 批量操作（批量删除、批量导入）
- ✅ 个人备注功能

**可选功能（P2）：**
- 🔶 批量回测
- 🔶 统计分析看板
- 🔶 价格提醒

### 1.3 非目标

本版本**不包含**以下功能：
- ❌ 复杂的技术指标实时计算（如实时MACD信号）
- ❌ 自动交易或模拟交易
- ❌ 港股、美股实时行情（仅支持A股）
- ❌ WebSocket实时推送（使用定时轮询）
- ❌ 移动端原生应用

### 1.4 设计原则

**简洁高效**: 操作流程简单，2步完成核心任务
**性能优先**: 50只自选股行情加载 < 2秒
**可扩展**: 预留扩展点，支持未来添加复杂功能
**用户体验**: 交互流畅，及时反馈，容错性强

---

## 2. 背景与动机

### 2.1 当前状态

**现有功能：**
- ✅ 用户可以通过搜索功能查找股票
- ✅ 用户可以发起单只股票的回测
- ✅ 基础的用户登录认证（预置账号）

**存在的问题：**
- ❌ 每次回测都需要重新搜索股票代码
- ❌ 无法管理关注的股票池
- ❌ 无法快速查看关注股票的行情
- ❌ 缺少用户粘性功能，无固定入口页面

### 2.2 为什么需要自选股

**散户核心需求：**
- 散户通常只关注10-50只股票
- 需要每日查看关注股票的行情变化
- 需要对不同类型股票分类管理（如"价值投资"、"短线机会"）
- 需要快速对关注股票进行回测验证

**系统价值：**
- 提升用户留存：成为用户每日访问的起点页面
- 提升回测效率：从自选股发起回测，避免重复输入
- 数据沉淀：为后续的智能推荐、组合优化提供基础

### 2.3 竞品对比

| 功能 | 同花顺 | 雪球 | 东方财富 | Stock Pal（本系统） |
|------|--------|------|----------|---------------------|
| 自选股基础管理 | ✅ | ✅ | ✅ | ✅ |
| 分组管理 | ✅ | ✅（组合） | ✅ | ✅ |
| 实时行情 | ✅ 毫秒级 | ✅ 分钟级 | ✅ 秒级 | ✅ 30秒-1分钟 |
| 快速回测 | ❌ | ❌ | ❌ | ✅（核心优势） |
| 批量回测 | ❌ | ❌ | ❌ | 🔶（未来） |

**差异化定位**: 深度整合回测功能，为量化散户服务

---

## 3. 总体架构设计

### 3.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │ WatchlistPage  │→ │ GroupManager   │→ │ QuickBacktest │ │
│  │  (主页)         │  │  (分组管理)     │  │  (快速回测)   │ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
│           ↓ API Calls (with JWT Token)                      │
└───────────────────────────┼─────────────────────────────────┘
                            │ HTTPS
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Backend (Flask)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   API Layer (RESTful)                   │ │
│  │  /api/v1/watchlist/*  |  /api/v1/watchlist/groups/*    │ │
│  └───────────────┬────────────────────────────────────────┘ │
│                  │ @jwt_required                             │
│  ┌───────────────▼────────────────────────────────────────┐ │
│  │                   Service Layer                         │ │
│  │  ┌──────────────────┐  ┌─────────────────────────────┐ │ │
│  │  │ WatchlistService │  │    QuoteService             │ │ │
│  │  │  - CRUD逻辑      │  │    - 行情获取               │ │ │
│  │  │  - 分组管理      │  │    - 缓存管理               │ │ │
│  │  │  - 权限验证      │  │    - 批量查询优化           │ │ │
│  │  └──────────────────┘  └─────────────────────────────┘ │ │
│  └───────────────┬───────────────┬────────────────────────┘ │
│                  │               │                           │
│  ┌───────────────▼───────────────▼────────────────────────┐ │
│  │                   Data Layer                            │ │
│  │  ┌──────────────────┐  ┌─────────────────────────────┐ │ │
│  │  │   PostgreSQL     │  │        Redis Cache          │ │ │
│  │  │  - watchlist_    │  │   - quote:{symbol}:data     │ │ │
│  │  │    groups        │  │   - quote:{symbol}:ttl      │ │ │
│  │  │  - watchlist_    │  │   - 交易时段: 30s-1min      │ │ │
│  │  │    stocks        │  │   - 非交易时段: 到收盘      │ │ │
│  │  └──────────────────┘  └─────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
│                  │                                            │
│  ┌───────────────▼────────────────────────────────────────┐ │
│  │              External Data Source                       │ │
│  │                   AkShare API                           │ │
│  │         ak.stock_zh_a_spot_em() - 实时行情              │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心模块

**WatchlistService（自选股服务）：**
- 职责：自选股和分组的CRUD操作
- 权限：所有操作必须验证 user_id，确保用户只能访问自己的数据
- 数据校验：股票代码格式、分组名称唯一性、重复添加检测

**QuoteService（行情服务）：**
- 职责：从AkShare获取实时行情、管理缓存
- 优化：批量获取、智能缓存、降级策略
- 容错：API失败时返回缓存数据或提示

### 3.3 数据流设计

#### 3.3.1 查看自选股列表流程

```
User → Frontend
    ↓
  GET /api/v1/watchlist
    ↓ (with JWT Token)
  API Layer (@jwt_required)
    ↓ extract user_id from token
  WatchlistService.get_user_watchlist(user_id)
    ↓ query database
  PostgreSQL: SELECT * FROM watchlist_stocks WHERE user_id = ?
    ↓ return stock list
  QuoteService.get_batch_quotes([stock_codes])
    ↓ check Redis cache
  Redis: GET quote:{symbol}:data
    ↓ if cache miss
  AkShare API: ak.stock_zh_a_spot_em()
    ↓ cache result
  Redis: SET quote:{symbol}:data (TTL: 30s-1min)
    ↓ merge data
  API Layer: format response
    ↓
  Frontend: render table
    ↓
  User sees watchlist with real-time quotes
```

#### 3.3.2 添加自选股流程

```
User → 点击"添加自选股"按钮
    ↓ 输入股票代码或搜索选择 + 选择分组
  POST /api/v1/watchlist
    body: { stock_code, stock_name, group_id?, note? }
    ↓ (with JWT Token)
  API Layer: validate request
    - stock_code format (6-digit)
    - group_id belongs to user (if provided)
    ↓
  WatchlistService.add_stock(user_id, stock_code, ...)
    ↓ check duplicate
  PostgreSQL: SELECT 1 FROM watchlist_stocks
              WHERE user_id = ? AND stock_code = ?
    ↓ if exists → return error
    ↓ if not exists → insert
  PostgreSQL: INSERT INTO watchlist_stocks (...)
    ↓ return success
  API Layer: return 201 Created
    ↓
  Frontend: update local state (optimistic update)
    ↓ show toast notification
  User sees stock added to list
```

#### 3.3.3 快速回测流程

```
User → 在自选股列表点击"回测"按钮
    ↓
  Frontend: navigate to /backtest
    query params: { symbol: stock_code }
    ↓
  BacktestPage: auto-fill stock_code
    - 保留用户上次使用的策略参数
    - 保留用户上次使用的时间范围
    ↓
  User: 调整参数（可选）→ 点击"开始回测"
    ↓
  POST /api/v1/backtest (existing API)
    ↓ ... (现有回测流程)
  Results displayed
```

---

## 4. 数据模型设计

### 4.1 数据库表设计

#### 4.1.1 自选股分组表 (watchlist_groups)

**表名**: `watchlist_groups`

**用途**: 存储用户创建的自选股分组

**字段设计**:

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGSERIAL | PRIMARY KEY | - | 分组ID（自增） |
| user_id | BIGINT | NOT NULL, FK | - | 所属用户ID |
| name | VARCHAR(50) | NOT NULL | - | 分组名称 |
| color | VARCHAR(20) | - | NULL | 颜色标签（hex或预设值） |
| sort_order | INTEGER | NOT NULL | 0 | 排序顺序（越小越靠前） |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 更新时间 |

**约束**:
- UNIQUE (user_id, name) - 同一用户下分组名称唯一
- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
- CHECK (sort_order >= 0)
- CHECK (length(name) > 0)

**索引**:
- PRIMARY KEY (id)
- INDEX idx_user_id (user_id)
- UNIQUE INDEX uk_user_group (user_id, name)

**预置数据**:
- 每个用户注册时自动创建默认分组"未分类"（sort_order=0，不可删除）

#### 4.1.2 自选股表 (watchlist_stocks)

**表名**: `watchlist_stocks`

**用途**: 存储用户的自选股票

**字段设计**:

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGSERIAL | PRIMARY KEY | - | 自选股记录ID |
| user_id | BIGINT | NOT NULL, FK | - | 所属用户ID |
| stock_code | VARCHAR(20) | NOT NULL | - | 股票代码（如600000） |
| stock_name | VARCHAR(50) | NOT NULL | - | 股票名称（如浦发银行） |
| group_id | BIGINT | FK, NULL | NULL | 所属分组ID（NULL=未分类） |
| note | TEXT | - | NULL | 个人备注 |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 添加时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 更新时间 |

**约束**:
- UNIQUE (user_id, stock_code) - 同一用户不能重复添加同一股票
- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
- FOREIGN KEY (group_id) REFERENCES watchlist_groups(id) ON DELETE SET NULL
- CHECK (stock_code ~ '^[0-9]{6}$') - 6位数字股票代码
- CHECK (length(stock_name) > 0)

**索引**:
- PRIMARY KEY (id)
- INDEX idx_user_id (user_id)
- INDEX idx_group_id (group_id)
- UNIQUE INDEX uk_user_stock (user_id, stock_code)
- INDEX idx_created_at (created_at) - 用于按添加时间排序

**数据生命周期**:
- 删除用户时级联删除（ON DELETE CASCADE）
- 删除分组时自选股不删除，group_id设为NULL（ON DELETE SET NULL）

### 4.2 数据关系图

```
┌─────────────────┐
│     users       │
│  (已存在表)      │
│ ┌─────────────┐ │
│ │ id (PK)     │ │
│ │ username    │ │
│ │ ...         │ │
│ └─────────────┘ │
└────────┬────────┘
         │ 1
         │
         │ N
    ┌────▼─────────────────┐
    │ watchlist_groups     │
    │ ┌──────────────────┐ │
    │ │ id (PK)          │ │
    │ │ user_id (FK)     │ │
    │ │ name (UNIQUE)    │ │
    │ │ color            │ │
    │ │ sort_order       │ │
    │ └──────────────────┘ │
    └──────┬───────────────┘
           │ 1
           │
           │ N
    ┌──────▼───────────────┐
    │ watchlist_stocks     │
    │ ┌──────────────────┐ │
    │ │ id (PK)          │ │
    │ │ user_id (FK)     │ │
    │ │ stock_code       │ │
    │ │ stock_name       │ │
    │ │ group_id (FK)    │ │
    │ │ note             │ │
    │ └──────────────────┘ │
    └──────────────────────┘
```

### 4.3 Redis缓存数据结构

**Key格式**: `quote:{symbol}:{field}`

**示例**:
```
quote:600000:data → JSON string
  {
    "code": "600000",
    "name": "浦发银行",
    "price": 8.52,
    "change_pct": 1.43,
    "volume": 12345678,
    "turnover_rate": 0.32,
    "timestamp": "2025-11-19 14:30:00"
  }

quote:batch:last_update → timestamp
  记录批量行情最后更新时间
```

**TTL策略**:
- 交易时段（9:30-15:00）: 30秒
- 非交易时段: 到当日收盘（4小时后过期）
- 周末/节假日: 到下一交易日开盘

---

## 5. API接口设计

### 5.1 API版本与认证

- **版本**: `/api/v1/`
- **认证**: 所有接口需要 JWT Token（通过 `@jwt_required` 装饰器）
- **用户隔离**: 自动从 Token 中提取 `user_id`，确保数据隔离

### 5.2 自选股管理接口

#### 5.2.1 获取自选股列表

```
GET /api/v1/watchlist
```

**Query参数**:
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| group_id | integer | 否 | - | 筛选指定分组（不传=全部） |
| sort_by | string | 否 | created_at | 排序字段：created_at, code, name |
| sort_order | string | 否 | desc | 排序方向：asc, desc |
| include_quotes | boolean | 否 | false | 是否包含实时行情 |

**请求头**:
```
Authorization: Bearer <JWT_TOKEN>
```

**响应示例** (200 OK):
```json
{
  "status": "success",
  "data": {
    "stocks": [
      {
        "id": 123,
        "stock_code": "600000",
        "stock_name": "浦发银行",
        "group_id": 5,
        "group_name": "银行板块",
        "note": "等待突破前高",
        "created_at": "2025-11-15T10:30:00Z",
        "quote": {  // 仅当 include_quotes=true 时存在
          "price": 8.52,
          "change_pct": 1.43,
          "volume": 12345678,
          "timestamp": "2025-11-19T14:30:00Z"
        }
      }
    ],
    "total": 25
  }
}
```

**错误响应**:
- 401 Unauthorized: Token无效或过期
- 400 Bad Request: 参数格式错误

#### 5.2.2 添加自选股

```
POST /api/v1/watchlist
```

**请求头**:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**请求体**:
```json
{
  "stock_code": "600000",
  "stock_name": "浦发银行",
  "group_id": 5,        // 可选，不传则加入"未分类"
  "note": "关注技术突破"  // 可选
}
```

**字段验证**:
- stock_code: 必需，6位数字，符合A股代码格式
- stock_name: 必需，非空字符串
- group_id: 可选，必须属于当前用户
- note: 可选，最长500字符

**响应示例** (201 Created):
```json
{
  "status": "success",
  "data": {
    "id": 124,
    "stock_code": "600000",
    "stock_name": "浦发银行",
    "group_id": 5,
    "note": "关注技术突破",
    "created_at": "2025-11-19T14:35:00Z"
  },
  "message": "自选股添加成功"
}
```

**错误响应**:
- 400 Bad Request: 参数验证失败
  ```json
  {
    "status": "error",
    "error": "股票代码格式错误",
    "code": "INVALID_STOCK_CODE"
  }
  ```
- 409 Conflict: 股票已存在
  ```json
  {
    "status": "error",
    "error": "该股票已在自选股中",
    "code": "STOCK_ALREADY_EXISTS"
  }
  ```

#### 5.2.3 更新自选股

```
PUT /api/v1/watchlist/{id}
```

**URL参数**:
- id: 自选股记录ID

**请求体**:
```json
{
  "group_id": 6,       // 可选：修改分组
  "note": "已突破"      // 可选：修改备注
}
```

**响应示例** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": 124,
    "stock_code": "600000",
    "stock_name": "浦发银行",
    "group_id": 6,
    "note": "已突破",
    "updated_at": "2025-11-19T15:00:00Z"
  },
  "message": "更新成功"
}
```

**错误响应**:
- 404 Not Found: 记录不存在或不属于当前用户
- 400 Bad Request: group_id不属于当前用户

#### 5.2.4 删除自选股

```
DELETE /api/v1/watchlist/{id}
```

**URL参数**:
- id: 自选股记录ID

**响应示例** (200 OK):
```json
{
  "status": "success",
  "message": "删除成功"
}
```

**错误响应**:
- 404 Not Found: 记录不存在或不属于当前用户

#### 5.2.5 批量删除自选股

```
DELETE /api/v1/watchlist/batch
```

**请求体**:
```json
{
  "ids": [123, 124, 125]
}
```

**字段验证**:
- ids: 必需，数组，至少1个元素，最多50个

**响应示例** (200 OK):
```json
{
  "status": "success",
  "data": {
    "deleted_count": 3
  },
  "message": "批量删除成功"
}
```

#### 5.2.6 批量导入自选股

```
POST /api/v1/watchlist/import
```

**请求体**:
```json
{
  "stocks": [
    { "stock_code": "600000", "stock_name": "浦发银行" },
    { "stock_code": "000001", "stock_name": "平安银行" }
  ],
  "group_id": 5,  // 可选：统一加入指定分组
  "skip_duplicates": true  // 可选：跳过已存在的股票（默认true）
}
```

**字段验证**:
- stocks: 必需，数组，至少1个，最多100个
- 每个stock需包含 stock_code 和 stock_name

**响应示例** (200 OK):
```json
{
  "status": "success",
  "data": {
    "imported_count": 2,
    "skipped_count": 0,
    "failed": []
  },
  "message": "导入完成"
}
```

#### 5.2.7 检查股票是否在自选股中

```
GET /api/v1/watchlist/check/{stock_code}
```

**用途**: 用于跨页面集成，判断某只股票是否已在当前用户的自选股中

**URL参数**:
- stock_code: 股票代码（6位数字）

**响应示例** (200 OK):
```json
{
  "status": "success",
  "data": {
    "in_watchlist": true,
    "watchlist_id": 123,  // 如果存在，返回记录ID
    "group_name": "银行板块"  // 如果存在，返回所属分组名称
  }
}
```

**不存在时**:
```json
{
  "status": "success",
  "data": {
    "in_watchlist": false
  }
}
```

**使用场景**:
- 回测页面：检查当前股票是否已添加，显示对应的按钮状态
- 股票搜索：在搜索结果中标记已添加的股票
- 回测结果页：检查回测股票是否已添加

**性能优化**:
- 该接口调用频繁，建议缓存结果（Redis，TTL 60秒）
- 批量检查可使用 POST 方法传入多个股票代码

### 5.3 分组管理接口

#### 5.3.1 获取分组列表

```
GET /api/v1/watchlist/groups
```

**Query参数**:
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| include_counts | boolean | 否 | false | 是否包含每组股票数量 |

**响应示例** (200 OK):
```json
{
  "status": "success",
  "data": {
    "groups": [
      {
        "id": 1,
        "name": "未分类",
        "color": "#999999",
        "sort_order": 0,
        "is_default": true,
        "stock_count": 5,  // 仅当 include_counts=true 时存在
        "created_at": "2025-11-01T10:00:00Z"
      },
      {
        "id": 5,
        "name": "银行板块",
        "color": "#1890ff",
        "sort_order": 1,
        "is_default": false,
        "stock_count": 8,
        "created_at": "2025-11-10T14:00:00Z"
      }
    ],
    "total": 2
  }
}
```

#### 5.3.2 创建分组

```
POST /api/v1/watchlist/groups
```

**请求体**:
```json
{
  "name": "科技板块",
  "color": "#52c41a",  // 可选
  "sort_order": 10    // 可选，默认为当前最大值+1
}
```

**字段验证**:
- name: 必需，1-50字符，当前用户下唯一
- color: 可选，hex颜色或预设值
- sort_order: 可选，非负整数

**响应示例** (201 Created):
```json
{
  "status": "success",
  "data": {
    "id": 10,
    "name": "科技板块",
    "color": "#52c41a",
    "sort_order": 10,
    "created_at": "2025-11-19T15:00:00Z"
  },
  "message": "分组创建成功"
}
```

**错误响应**:
- 409 Conflict: 分组名称已存在
  ```json
  {
    "status": "error",
    "error": "分组名称已存在",
    "code": "GROUP_NAME_EXISTS"
  }
  ```

#### 5.3.3 更新分组

```
PUT /api/v1/watchlist/groups/{id}
```

**请求体**:
```json
{
  "name": "科技龙头",    // 可选
  "color": "#722ed1",   // 可选
  "sort_order": 2      // 可选
}
```

**响应示例** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": 10,
    "name": "科技龙头",
    "color": "#722ed1",
    "sort_order": 2,
    "updated_at": "2025-11-19T15:10:00Z"
  },
  "message": "更新成功"
}
```

#### 5.3.4 删除分组

```
DELETE /api/v1/watchlist/groups/{id}
```

**行为**:
- 删除分组本身
- 分组内的股票 group_id 设为 NULL（移至"未分类"）
- 不能删除默认分组"未分类"

**响应示例** (200 OK):
```json
{
  "status": "success",
  "message": "分组已删除，内含股票已移至未分类"
}
```

**错误响应**:
- 400 Bad Request: 尝试删除默认分组
  ```json
  {
    "status": "error",
    "error": "不能删除默认分组",
    "code": "CANNOT_DELETE_DEFAULT_GROUP"
  }
  ```

### 5.4 实时行情接口

#### 5.4.1 批量获取行情

```
GET /api/v1/watchlist/quotes
```

**Query参数**:
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| codes | string | 否 | - | 股票代码列表（逗号分隔），不传则获取全部自选股 |

**响应示例** (200 OK):
```json
{
  "status": "success",
  "data": {
    "quotes": [
      {
        "code": "600000",
        "name": "浦发银行",
        "price": 8.52,
        "change_pct": 1.43,
        "change_amount": 0.12,
        "volume": 12345678,
        "turnover": 105234567.89,
        "turnover_rate": 0.32,
        "high": 8.55,
        "low": 8.42,
        "open": 8.45,
        "pre_close": 8.40,
        "timestamp": "2025-11-19T14:30:00Z"
      }
    ],
    "total": 1,
    "cache_hit_rate": 0.85,  // 缓存命中率
    "data_source": "akshare",
    "market_status": "trading"  // trading | closed | pre_market
  }
}
```

**错误响应**:
- 503 Service Unavailable: 数据源不可用
  ```json
  {
    "status": "error",
    "error": "行情数据暂时不可用，请稍后重试",
    "code": "QUOTE_SERVICE_UNAVAILABLE"
  }
  ```

#### 5.4.2 获取统计数据

```
GET /api/v1/watchlist/stats
```

**响应示例** (200 OK):
```json
{
  "status": "success",
  "data": {
    "total_stocks": 25,
    "groups": [
      { "group_id": 1, "group_name": "未分类", "count": 5 },
      { "group_id": 5, "group_name": "银行板块", "count": 8 }
    ],
    "today_stats": {
      "up_count": 15,
      "down_count": 8,
      "flat_count": 2,
      "avg_change_pct": 0.52
    }
  }
}
```

### 5.5 错误响应统一格式

所有API错误响应遵循统一格式：

```json
{
  "status": "error",
  "error": "错误描述信息",
  "code": "ERROR_CODE",
  "details": {  // 可选：额外的错误细节
    "field": "stock_code",
    "value": "12345",
    "reason": "股票代码必须为6位数字"
  }
}
```

**常见错误码**:
- `INVALID_STOCK_CODE`: 股票代码格式错误
- `STOCK_ALREADY_EXISTS`: 股票已在自选股中
- `GROUP_NOT_FOUND`: 分组不存在
- `GROUP_NAME_EXISTS`: 分组名称重复
- `CANNOT_DELETE_DEFAULT_GROUP`: 不能删除默认分组
- `QUOTE_SERVICE_UNAVAILABLE`: 行情服务不可用
- `UNAUTHORIZED`: 未授权
- `INVALID_TOKEN`: Token无效

---

## 6. 实时行情方案

### 6.1 数据源选择

**主数据源**: AkShare

**API函数**: `ak.stock_zh_a_spot_em()`

**返回字段**（选择使用）:
- 代码、名称
- 最新价、涨跌幅、涨跌额
- 成交量、成交额、换手率
- 最高、最低、今开、昨收

**优点**:
- ✅ 免费开源
- ✅ 数据较准确（来自东方财富）
- ✅ 已在系统中使用，无新依赖

**缺点**:
- ❌ 延迟约30秒-1分钟
- ❌ 可能存在限流风险
- ❌ 无WebSocket推送

### 6.2 缓存策略

#### 6.2.1 缓存层次

**L1缓存（Redis）:**
- 用途：存储实时行情数据
- TTL: 动态调整（见下文）
- Key格式: `quote:{symbol}:data`
- 数据格式: JSON字符串

**L2缓存（应用内存）:**
- 用途：交易时段判断结果（避免重复计算）
- TTL: 60秒
- Key: `market_status`
- Value: `trading` | `closed` | `pre_market`

#### 6.2.2 动态TTL策略

```
交易时段判断逻辑：
- 工作日 9:30-11:30, 13:00-15:00 → trading
- 工作日其他时间 → closed
- 周末/节假日 → closed

TTL策略：
IF market_status == 'trading':
    TTL = 30 seconds  # 交易时段频繁更新
ELIF market_status == 'closed':
    IF 当前时间 < 今日收盘时间:
        TTL = 到今日收盘时间  # 盘前/午休保留到收盘
    ELSE:
        TTL = 4 hours  # 盘后数据保留到晚上
```

#### 6.2.3 批量获取优化

**问题**: 用户自选股可能有50+只，逐个查询效率低

**解决方案**:

1. **批量查询AkShare**:
   - `ak.stock_zh_a_spot_em()` 返回全市场行情
   - 一次性获取，过滤出所需股票
   - 比逐个查询快10倍以上

2. **分批缓存更新**:
   - 检查Redis中哪些股票已缓存且未过期
   - 只请求AkShare获取缺失/过期的股票
   - 减少API调用次数

3. **异步预热**（可选，P2）:
   - 定时任务每30秒获取热门股票行情
   - 用户访问时直接命中缓存

### 6.3 降级策略

**场景1: AkShare API不可用**
- 返回缓存数据（即使过期）
- 响应中标注 `"data_stale": true`
- 前端显示"行情数据可能延迟"提示

**场景2: Redis不可用**
- 直接调用AkShare，不缓存
- 性能下降但功能可用
- 记录错误日志，触发告警

**场景3: 部分股票查询失败**
- 返回成功的股票行情
- 失败的股票标注为 `null`
- 前端显示"--"或"暂无数据"

### 6.4 交易时段判断

**A股交易时段**:
- 集合竞价: 9:15-9:25（暂不支持）
- 连续竞价: 9:30-11:30, 13:00-15:00
- 收盘集合竞价: 14:57-15:00（深市）

**节假日判断**:
- 使用 `chinese_calendar` 库判断工作日
- 缓存到本地配置（减少依赖）

**实现方式**:
- 工具函数: `is_trading_time(datetime) -> bool`
- 缓存结果60秒（避免重复计算）

### 6.5 前端轮询策略

**交易时段**:
- 页面加载时立即获取行情
- 定时轮询: 每60秒自动刷新
- 用户可手动刷新

**非交易时段**:
- 页面加载时获取一次
- 不自动刷新（节省资源）
- 显示"非交易时段"标识

**优化**:
- 页面不可见时（tab切换）暂停轮询
- 页面恢复可见时立即刷新一次
- 使用 `document.visibilityState` API

---

## 7. 前端设计

### 7.1 页面结构与导航设计

#### 7.1.1 自选股作为新首页（推荐方案）

**设计理念**:
- 自选股是散户最常用功能，应该是用户每日访问的起点
- 参考同花顺、雪球，都以自选股/持仓作为首页
- 提升自选股功能使用率，增强用户粘性

**路由调整**:
```
/                                   # 根路径
  ├─ 已登录 → 重定向到 /watchlist
  └─ 未登录 → 重定向到 /login

/watchlist                          # 自选股主页（新的首页）
  ├─ /watchlist?group={id}         # 按分组筛选
  └─ /watchlist/import              # 批量导入页面（可选）

/backtest                           # 回测页面
/strategies                         # 策略管理页面（未来）
/profile                            # 个人中心
/login                              # 登录页
```

**导航栏设计**:
```
┌─────────────────────────────────────────────────────────┐
│ Stock Pal    [自选股] [回测] [策略] [我的]    用户头像 ▼ │
└─────────────────────────────────────────────────────────┘
```

- **移除"主页"**：自选股本身就是主页
- **自选股放首位**：强化其核心地位
- **突出显示**：当前页面加粗/下划线标识

#### 7.1.2 原主页处理

**方案A：移除主页**（推荐）
- 原主页功能移至"关于"页面（/about）
- 首次访问用户显示引导弹窗

**方案B：保留主页作为产品介绍页**（备选）
- 仅对未登录用户显示
- 已登录用户不再访问主页
- 主页路径改为 `/welcome` 或 `/intro`

### 7.2 组件架构

```
WatchlistPage (主容器)
├─ WatchlistHeader (顶部操作栏)
│  ├─ AddStockButton (添加按钮 → 打开Modal)
│  ├─ ImportButton (批量导入)
│  ├─ RefreshButton (刷新行情)
│  └─ SearchInput (搜索过滤)
│
├─ GroupFilter (分组筛选栏)
│  ├─ GroupTab ("全部" | "未分类" | "银行板块" ...)
│  └─ GroupManageButton (管理分组 → 打开Modal)
│
├─ WatchlistTable (主表格)
│  ├─ StockRow (单行)
│  │  ├─ StockBasicInfo (代码、名称)
│  │  ├─ QuoteInfo (价格、涨跌幅)
│  │  ├─ GroupTag (分组标签)
│  │  ├─ NoteCell (备注)
│  │  └─ ActionButtons
│  │     ├─ BacktestButton (快速回测)
│  │     ├─ EditButton (编辑)
│  │     └─ DeleteButton (删除)
│  │
│  └─ BatchActionBar (批量操作栏，多选时显示)
│     ├─ BatchDeleteButton
│     └─ BatchMoveButton (批量移动到分组)
│
└─ Modals
   ├─ AddStockModal (添加自选股)
   │  ├─ StockSearchInput (搜索股票)
   │  ├─ GroupSelect (选择分组)
   │  └─ NoteInput (可选备注)
   │
   ├─ GroupManageModal (分组管理)
   │  ├─ GroupList (分组列表)
   │  ├─ CreateGroupForm (新建分组)
   │  └─ EditGroupForm (编辑分组)
   │
   └─ ImportModal (批量导入)
      ├─ TextArea (粘贴股票代码)
      └─ GroupSelect (选择目标分组)
```

### 7.3 跨页面集成与入口设计

自选股功能需要与现有页面深度集成，提供多个便捷入口。

#### 7.3.1 回测页面集成

**添加到自选股按钮**:

**位置**：回测页面顶部，股票代码输入框右侧

```
┌────────────────────────────────────────────────────┐
│  股票搜索: [600000 浦发银行 ▼]  [添加到自选股 ⭐]  │
│                                                    │
│  策略选择: [均线交叉 ▼]        [开始回测]          │
└────────────────────────────────────────────────────┘
```

**交互逻辑**:
1. **未添加状态**：
   - 按钮文案："添加到自选股"
   - 图标：空心星 ⭐
   - 颜色：次要按钮（灰色/蓝色边框）

2. **已添加状态**：
   - 按钮文案："已在自选股"
   - 图标：实心星 ★
   - 颜色：主题色（金色/黄色）
   - 悬停提示："点击可移除"

3. **点击行为**：
   - 未添加 → 弹出快速添加下拉菜单：
     ```
     选择分组：
     ○ 未分类
     ○ 银行板块
     ○ 价值投资
     ─────────────
     [+ 新建分组]

     [确定]  [取消]
     ```
   - 已添加 → 二次确认后移除

**状态同步**:
- 添加成功后，按钮状态立即更新（乐观更新）
- 失败时回滚并显示错误提示

#### 7.3.2 股票搜索结果集成

**位置**：股票搜索下拉列表每一项的右侧

```
┌──────────────────────────────────────┐
│ 搜索结果：                            │
│  600000 浦发银行          [⭐]        │
│  000001 平安银行          [★] 已添加 │
│  600036 招商银行          [⭐]        │
│  600519 贵州茅台          [⭐]        │
└──────────────────────────────────────┘
```

**交互细节**:
- 星标图标大小：16px
- 悬停时显示提示："添加到自选股" / "已在自选股"
- 点击星标 → 直接添加到"未分类"分组（快速操作）
- 成功后图标变为实心星，显示1秒Toast："已添加到自选股"

**实现要点**:
- 搜索结果需要包含 `in_watchlist: boolean` 字段
- 后端API需要返回该字段（基于当前用户）

#### 7.3.3 回测结果页集成

**位置**：回测结果页顶部面包屑/标题区域

```
┌────────────────────────────────────────────────────┐
│  回测结果                                          │
│  ┌──────────────────────────────────────────────┐ │
│  │ 600000 浦发银行  [添加到自选股 ⭐]            │ │
│  │ 策略：均线交叉  |  时间：2023-01-01 ~ 2024-01-01│ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  收益率: +15.2%  最大回撤: -8.5%  ...             │
└────────────────────────────────────────────────────┘
```

**用户场景**:
- 用户完成回测后，觉得策略效果不错
- 直接添加该股票到自选股，方便后续跟踪

#### 7.3.4 自选股页面内的快速回测

**位置**：自选股列表每一行的操作列

```
┌─────────────────────────────────────────────────────────┐
│ 代码    名称      分组     当前价   涨跌幅   操作         │
│ 600000  浦发银行  银行板块  8.52    +1.43%  [回测][编辑][删除] │
│ 000001  平安银行  银行板块  12.35   -0.52%  [回测][编辑][删除] │
└─────────────────────────────────────────────────────────┘
```

**回测按钮交互**:
1. 点击"回测"按钮
2. 跳转到 `/backtest?symbol=600000`
3. 回测页面自动填充：
   - 股票代码：600000
   - 股票名称：浦发银行
   - 保留用户上次使用的策略和参数
   - 时间范围：默认最近1年

**返回导航**:
- 回测页面显示"返回自选股"按钮（浏览器历史来自自选股时显示）
- 点击后返回自选股列表，保持之前的筛选/排序状态

#### 7.3.5 新用户引导设计

**首次登录流程**:

```
1. 用户登录成功
   ↓
2. 检测是否首次登录（自选股为空）
   ↓ 是
3. 显示引导弹窗
   ┌────────────────────────────────────────┐
   │  欢迎使用 Stock Pal！                   │
   │                                        │
   │  [图标：自选股]                         │
   │                                        │
   │  建议先添加几只关注的股票到自选股，      │
   │  这样可以：                             │
   │  ✓ 快速发起回测，无需重复搜索            │
   │  ✓ 查看实时行情                         │
   │  ✓ 使用分组管理不同类型的股票            │
   │                                        │
   │  [立即添加自选股]  [跳过，稍后添加]      │
   └────────────────────────────────────────┘
   ↓
4a. 点击"立即添加"
   → 跳转到自选股页面
   → 高亮显示"添加"按钮（闪烁动画）
   → 打开添加自选股Modal

4b. 点击"跳过"
   → 正常进入自选股页面
   → 显示空状态引导
```

**空状态引导**（自选股为空时）:

```
┌─────────────────────────────────────────┐
│                                         │
│          [大图标：空文件夹]              │
│                                         │
│        还没有添加自选股                  │
│                                         │
│   添加你关注的股票，开始量化投资之旅！    │
│                                         │
│       [+ 添加第一只自选股]               │
│                                         │
└─────────────────────────────────────────┘
```

**首次添加成功提示**（添加第一只股票后）:

```
Toast通知（3秒后自动消失）：
┌────────────────────────────────────────┐
│ ✓ 添加成功！                            │
│                                        │
│  你可以：                               │
│  • 点击"回测"按钮快速发起回测            │
│  • 查看实时行情                         │
│  • 创建分组管理不同类型的股票            │
└────────────────────────────────────────┘
```

**引导步骤设计**（可选，渐进式引导）:

1. **Step 1**：添加第一只股票
   - 高亮"添加"按钮
   - 提示气泡："点击这里添加股票"

2. **Step 2**：完成添加后
   - 高亮"回测"按钮
   - 提示气泡："点击这里对该股票进行回测"

3. **Step 3**：添加3只股票后
   - 高亮"管理分组"按钮
   - 提示气泡："试试用分组管理你的自选股"

4. **完成引导**：
   - 显示祝贺弹窗
   - 标记引导完成（存储到用户偏好设置）

#### 7.3.6 全局入口总结

自选股功能的入口分布：

| 入口位置 | 触发方式 | 目标操作 | 优先级 |
|---------|---------|---------|--------|
| 导航栏 | 点击"自选股" | 进入自选股页面 | P0 |
| 登录成功 | 自动跳转 | 进入自选股页面（新首页） | P0 |
| 回测页面 | 点击"添加"按钮 | 添加当前股票到自选股 | P0 |
| 搜索结果 | 点击星标图标 | 快速添加到未分类 | P1 |
| 回测结果页 | 点击"添加"按钮 | 添加回测股票到自选股 | P1 |
| 首次登录 | 引导弹窗 | 引导用户添加自选股 | P1 |

### 7.4 状态管理

**使用方案**: Zustand（轻量级状态管理）

**State结构**:

```typescript
interface WatchlistState {
  // 数据状态
  stocks: WatchlistStock[]
  groups: WatchlistGroup[]
  quotes: Map<string, StockQuote>

  // UI状态
  selectedGroupId: number | null  // 当前筛选的分组
  selectedStockIds: Set<number>   // 批量选中的股票
  searchKeyword: string           // 搜索关键词
  sortBy: 'code' | 'name' | 'created_at' | 'change_pct'
  sortOrder: 'asc' | 'desc'

  // 加载状态
  isLoading: boolean
  isRefreshingQuotes: boolean

  // Actions
  fetchWatchlist: () => Promise<void>
  addStock: (stock: AddStockDTO) => Promise<void>
  deleteStock: (id: number) => Promise<void>
  updateStock: (id: number, updates: Partial<Stock>) => Promise<void>

  fetchGroups: () => Promise<void>
  createGroup: (group: CreateGroupDTO) => Promise<void>
  updateGroup: (id: number, updates: Partial<Group>) => Promise<void>
  deleteGroup: (id: number) => Promise<void>

  refreshQuotes: () => Promise<void>

  // UI Actions
  setSelectedGroup: (groupId: number | null) => void
  toggleStockSelection: (id: number) => void
  setSearchKeyword: (keyword: string) => void
}
```

**数据流**:
1. 组件挂载 → `fetchWatchlist()` + `fetchGroups()`
2. 添加股票 → `addStock()` → 乐观更新UI → API调用 → 成功后刷新行情
3. 定时刷新 → `refreshQuotes()` → 仅更新 `quotes` Map
4. 筛选/排序 → 计算属性（derived state）

### 7.5 表格设计

**列配置**:

| 列名 | 宽度 | 排序 | 说明 |
|------|------|------|------|
| 多选框 | 50px | - | 批量操作 |
| 股票代码 | 100px | ✅ | 可点击跳转回测页 |
| 股票名称 | 150px | ✅ | - |
| 分组 | 100px | - | Tag显示，可快速筛选 |
| 当前价 | 100px | - | 红涨绿跌 |
| 涨跌幅 | 100px | ✅ | 百分比，红涨绿跌 |
| 成交量 | 120px | - | 万手 |
| 备注 | 200px | - | 悬停显示完整内容 |
| 添加时间 | 150px | ✅ | 相对时间（2天前） |
| 操作 | 150px | - | 回测/编辑/删除按钮 |

**交互细节**:
- 表头固定（sticky header）
- 行高: 48px
- 悬停高亮
- 涨跌幅使用渐变背景色（涨多越红，跌多越绿）
- 支持Ctrl/Cmd多选
- 支持拖拽排序（可选，P2）

### 7.6 响应式设计

**桌面端（>= 1024px）**:
- 表格视图，显示完整列
- 左侧分组筛选栏（侧边栏）

**平板端（768px - 1023px）**:
- 表格视图，隐藏部分列（备注、成交量）
- 分组筛选改为顶部Tab

**移动端（< 768px）**:
- 卡片视图，每张卡片显示：
  - 代码、名称
  - 当前价、涨跌幅（大字号）
  - 分组Tag
  - 快速回测按钮
- 分组筛选改为下拉选择

### 7.7 加载与错误处理

**加载状态**:
- 首次加载: 全屏Skeleton（骨架屏）
- 刷新行情: 表格不动，显示加载指示器
- 添加/删除: 局部加载动画

**错误处理**:
- API失败: Toast提示 + 重试按钮
- 行情获取失败: 显示"--"，不影响其他列
- 网络断开: 顶部Banner提示

**空状态**:
- 无自选股: 引导用户添加（大图标 + 文案 + 快速添加按钮）
- 搜索无结果: "未找到匹配的股票"

### 7.8 性能优化

**虚拟滚动**:
- 自选股 > 50只时启用
- 使用 `react-window` 或 `react-virtualized`

**防抖搜索**:
- 搜索输入防抖300ms

**乐观更新**:
- 添加/删除操作立即更新UI
- API失败时回滚

**Memo优化**:
- `React.memo()` 包装行组件
- 使用 `useMemo` 缓存过滤/排序结果

---

## 8. 安全与权限

### 8.1 认证机制

**JWT Token验证**:
- 所有API接口使用 `@jwt_required` 装饰器
- Token过期时间: 24小时
- Refresh Token机制（复用用户账户系统）

**用户隔离**:
- 自动从 Token 中提取 `user_id`
- 所有数据库查询必须加 `WHERE user_id = ?`
- 防止用户访问他人数据

### 8.2 输入验证

**股票代码**:
- 格式: 6位数字
- 范围: 0-9
- 正则: `^[0-9]{6}$`

**分组名称**:
- 长度: 1-50字符
- 禁止字符: 特殊字符（防止SQL注入）
- 同用户下唯一性检查

**备注内容**:
- 长度: 最多500字符
- 过滤XSS攻击：HTML转义

### 8.3 权限控制

**数据访问权限**:
- 用户只能访问自己的自选股和分组
- 删除/更新操作前验证所有权

**默认分组保护**:
- "未分类"分组不可删除
- 系统级分组标记 `is_default=true`

### 8.4 SQL注入防护

**使用参数化查询**:
- 所有SQL使用 SQLAlchemy ORM
- 避免字符串拼接
- 用户输入作为参数绑定

**示例**:
```
❌ 错误：
  query = f"SELECT * FROM stocks WHERE code = '{code}'"

✅ 正确：
  query = session.query(Stock).filter(Stock.code == code)
```

### 8.5 速率限制

**API限流**:
- 添加自选股: 100次/小时/用户
- 批量导入: 10次/小时/用户
- 获取行情: 600次/小时/用户（约每分钟10次）

**实现方式**:
- 使用 `flask-limiter`
- 基于 user_id 限流
- Redis存储计数器

---

## 9. 性能优化方案

### 9.1 数据库优化

**索引策略**:
- `(user_id, stock_code)` 复合索引（查询重复）
- `(user_id, group_id)` 复合索引（按分组筛选）
- `created_at` 单列索引（按时间排序）

**查询优化**:
- 使用 JOIN 一次性获取股票 + 分组信息
- 避免 N+1 查询
- 使用 `LIMIT` 分页（未来）

**连接池**:
- 最小连接: 5
- 最大连接: 20
- 超时时间: 30秒

### 9.2 缓存优化

**Redis缓存命中率目标**: > 85%

**缓存预热**:
- 用户登录时预加载自选股列表
- 定时任务预热热门股票行情

**缓存失效**:
- 自选股增删改 → 清除用户自选股缓存
- 分组增删改 → 清除用户分组缓存
- 行情缓存按TTL自动过期

### 9.3 API性能目标

| 接口 | P95响应时间 | 并发能力 |
|------|------------|----------|
| 获取自选股列表（无行情） | < 200ms | 100 QPS |
| 获取自选股列表（含行情） | < 2s | 50 QPS |
| 添加自选股 | < 300ms | 50 QPS |
| 删除自选股 | < 200ms | 50 QPS |
| 批量获取行情 | < 3s (50只) | 20 QPS |

### 9.4 前端性能优化

**首屏加载**:
- 代码分割: 自选股页面单独bundle
- 懒加载: Modal组件按需加载
- 骨架屏: 减少白屏时间

**运行时性能**:
- 虚拟滚动: 渲染可视区域
- Debounce: 搜索、排序
- Throttle: 滚动事件

**网络优化**:
- 接口合并: 一次请求获取股票+行情
- 请求取消: 切换分组时取消上次请求
- 预加载: 鼠标悬停在Tab时预加载数据

---

## 10. 实施计划

### 10.1 总体时间线

**总工期**: 10-12天（1人）

**里程碑**:
- Phase 1 (Day 1-5): 后端MVP + 数据库
- Phase 2 (Day 6-8): 前端MVP
- Phase 3 (Day 9-10): 实时行情集成
- Phase 4 (Day 11-12): 测试与优化

### 10.2 Phase 1: 后端MVP（5天）

**Day 1-2: 数据库与基础服务**
- [x] 创建数据库表（watchlist_groups, watchlist_stocks）
- [x] 编写数据库迁移脚本
- [x] 实现 WatchlistService 基础类
  - get_user_watchlist()
  - add_stock()
  - delete_stock()
  - update_stock()
- [x] 编写单元测试

**Day 3-4: API接口开发**
- [x] 实现自选股管理接口
  - GET /api/v1/watchlist
  - POST /api/v1/watchlist
  - PUT /api/v1/watchlist/{id}
  - DELETE /api/v1/watchlist/{id}
- [x] 实现分组管理接口
  - GET /api/v1/watchlist/groups
  - POST /api/v1/watchlist/groups
  - PUT /api/v1/watchlist/groups/{id}
  - DELETE /api/v1/watchlist/groups/{id}
- [x] 请求验证与错误处理
- [x] 编写API测试

**Day 5: 批量操作与优化**
- [x] 实现批量删除接口
- [x] 实现批量导入接口
- [x] 添加数据库索引
- [x] 性能测试与调优

**交付物**:
- ✅ 完整的后端API（无行情功能）
- ✅ 数据库表与索引
- ✅ 单元测试覆盖率 > 80%

### 10.3 Phase 2: 前端MVP（3天）

**Day 6: 基础页面与组件**
- [x] 创建 WatchlistPage 主页面
- [x] 实现 WatchlistTable 表格组件
- [x] 实现 GroupFilter 分组筛选
- [x] 实现 AddStockModal 添加弹窗
- [x] 设置状态管理（Zustand store）

**Day 7: 交互功能**
- [x] 实现添加/删除自选股
- [x] 实现编辑功能（修改分组、备注）
- [x] 实现分组管理Modal
- [x] 实现搜索、排序、筛选

**Day 8: 批量操作、跨页面集成与优化**
- [x] 实现批量选择与删除
- [x] 实现批量导入功能
- [x] **跨页面集成**：
  - [x] 回测页面：添加"添加到自选股"按钮
  - [x] 股票搜索：添加星标图标
  - [x] 回测结果页：添加"添加到自选股"按钮
  - [x] 自选股列表：快速回测跳转
- [x] **新用户引导**：
  - [x] 首次登录引导弹窗
  - [x] 空状态引导页面
- [x] **导航调整**：
  - [x] 自选股作为新首页（路由重定向）
  - [x] 更新导航栏布局
- [x] 添加加载状态与错误处理
- [x] 响应式适配

**交付物**:
- ✅ 完整的自选股管理页面（无行情）
- ✅ 所有CRUD功能可用
- ✅ 跨页面集成完成（回测页、搜索、结果页）
- ✅ 新用户引导流程可用
- ✅ 导航栏调整完成
- ✅ 基础交互体验良好

### 10.4 Phase 3: 实时行情集成（2天）

**Day 9: 后端行情服务**
- [x] 实现 QuoteService
  - get_single_quote()
  - get_batch_quotes()
  - 集成AkShare API
- [x] 实现Redis缓存
  - 动态TTL策略
  - 交易时段判断
- [x] 实现行情API接口
  - GET /api/v1/watchlist/quotes
- [x] 降级策略实现

**Day 10: 前端行情展示**
- [x] 在表格中集成行情显示
- [x] 实现定时刷新（60秒轮询）
- [x] 实现手动刷新按钮
- [x] 涨跌幅颜色标识
- [x] 交易时段判断逻辑

**交付物**:
- ✅ 实时行情功能可用
- ✅ 缓存命中率 > 80%
- ✅ 50只股票行情加载 < 2秒

### 10.5 Phase 4: 测试与优化（2天）

**Day 11: 集成测试**
- [x] 端到端测试（E2E）
- [x] 性能测试（负载测试）
- [x] 边界条件测试
- [x] 修复发现的Bug

**Day 12: 优化与上线准备**
- [x] 性能优化（针对测试发现的瓶颈）
- [x] 安全检查（SQL注入、XSS防护）
- [x] 文档完善（API文档、用户指南）
- [x] 部署到测试环境

**交付物**:
- ✅ 所有测试通过
- ✅ 性能指标达标
- ✅ 系统可上线

### 10.6 依赖关系

**前置条件**:
- ✅ 用户账户系统已完成（BL-003）
- ✅ JWT认证机制可用
- ✅ Redis服务已部署

**并行开发**:
- 后端API开发 与 前端组件开发可并行
- 使用Mock数据进行前端开发
- API完成后进行联调

**阻塞风险**:
- AkShare API不稳定 → 准备备用数据源
- Redis部署延迟 → 先用内存缓存

---

## 11. 测试策略

### 11.1 单元测试

**后端（Pytest）**:

**WatchlistService测试**:
- ✅ test_add_stock_success
- ✅ test_add_stock_duplicate
- ✅ test_get_watchlist_by_user
- ✅ test_delete_stock_success
- ✅ test_update_stock_group
- ✅ test_user_isolation (不能访问他人股票)

**QuoteService测试**:
- ✅ test_get_single_quote_cache_hit
- ✅ test_get_single_quote_cache_miss
- ✅ test_get_batch_quotes_performance
- ✅ test_dynamic_ttl_trading_hours
- ✅ test_dynamic_ttl_non_trading
- ✅ test_fallback_when_api_fails

**API测试**:
- ✅ test_api_requires_authentication
- ✅ test_add_watchlist_validation
- ✅ test_delete_watchlist_not_found
- ✅ test_create_group_duplicate_name
- ✅ test_delete_default_group_forbidden

**覆盖率目标**: > 80%

**前端（Jest + React Testing Library）**:
- ✅ test_watchlist_table_renders
- ✅ test_add_stock_modal
- ✅ test_delete_stock_confirmation
- ✅ test_group_filter_changes
- ✅ test_search_filters_stocks
- ✅ test_batch_selection

### 11.2 集成测试

**端到端场景**:
1. **用户登录 → 查看空自选股 → 添加股票 → 刷新行情**
2. **创建分组 → 添加股票到分组 → 筛选分组**
3. **批量导入 → 查看列表 → 批量删除**
4. **添加股票 → 快速回测 → 返回自选股**
5. **非交易时段访问 → 不自动刷新**

**工具**: Playwright 或 Cypress

### 11.3 性能测试

**负载测试场景**:
- 100用户并发访问自选股列表
- 50用户同时刷新行情
- 单用户自选股数量 100+

**性能指标验证**:
- 响应时间 P95 < 目标值
- 缓存命中率 > 85%
- 数据库连接池无泄漏

**工具**: Locust 或 JMeter

### 11.4 安全测试

**测试项**:
- ✅ SQL注入测试（使用sqlmap）
- ✅ XSS攻击测试（输入恶意脚本）
- ✅ JWT Token伪造测试
- ✅ 越权访问测试（尝试访问他人数据）
- ✅ 速率限制测试（暴力请求）

### 11.5 兼容性测试

**浏览器**:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**设备**:
- Desktop (1920x1080, 1366x768)
- Tablet (iPad)
- Mobile (iPhone, Android)

---

## 12. 风险与挑战

### 12.1 技术风险

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| AkShare API不稳定 | 高 | 中 | 1. 实现降级策略（返回缓存） 2. 准备备用数据源（新浪、东方财富） |
| 行情延迟过大 | 中 | 中 | 1. 明确标注"延迟约1分钟" 2. 优化缓存策略 |
| 数据库性能瓶颈 | 高 | 低 | 1. 合理设计索引 2. 读写分离（未来） |
| Redis单点故障 | 中 | 低 | 1. 降级到直接查询 2. 部署Redis集群（未来） |
| 前端虚拟滚动实现复杂 | 低 | 中 | 1. 使用成熟库（react-window） 2. P2优先级，可后置 |

### 12.2 业务风险

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| 用户自选股数量过多 | 中 | 低 | 1. 设置上限（200只） 2. 提示优化建议 |
| 分组管理过于复杂 | 中 | 中 | 1. 简化UI 2. 提供默认分组模板 |
| 用户不使用分组功能 | 低 | 中 | 1. 默认分组已满足需求 2. 通过引导提升使用率 |
| 实时行情期望过高 | 高 | 高 | 1. 明确标注"延迟1分钟" 2. 不承诺秒级更新 |

### 12.3 时间风险

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| 用户账户系统延迟 | 高 | 低 | 1. 并行开发Mock认证 2. 协调优先级 |
| AkShare集成比预期复杂 | 中 | 中 | 1. 预留buffer时间 2. 简化P2功能 |
| 性能优化超时 | 中 | 中 | 1. MVP先上线 2. 迭代优化 |

### 12.4 数据质量风险

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| 股票代码错误 | 中 | 低 | 1. 输入验证 2. 与AkShare校验 |
| 行情数据异常值 | 低 | 低 | 1. 数据清洗 2. 异常检测 |
| 停牌股票行情缺失 | 低 | 中 | 1. 显示"停牌" 2. 返回最后交易日数据 |

---

## 13. 未来扩展

### 13.1 短期优化（1-3个月）

**智能推荐**:
- 基于回测历史推荐相似股票
- 同行业股票推荐

**技术指标信号**:
- 在列表直接显示MA趋势（上/下/横盘）
- 显示MACD金叉/死叉信号
- 显示RSI超买/超卖

**消息提醒**:
- 价格突破提醒（突破前高/前低）
- 技术指标信号提醒
- 公告/财报提醒

### 13.2 中期扩展（3-6个月）

**批量回测**:
- 勾选多只股票，统一策略回测
- 生成对比报告，筛选最佳标的

**行业板块分析**:
- 查看自选股行业分布
- 行业整体涨跌统计
- 板块轮动分析

**组合管理**:
- 自选股转为投资组合
- 设置目标仓位
- 组合收益模拟

### 13.3 长期愿景（6个月+）

**跨市场支持**:
- 港股自选股（港股通）
- 美股自选股（ADR）

**实时推送**:
- WebSocket实时行情
- 秒级更新

**AI辅助**:
- 智能分组建议
- 风险提示
- 买卖时机推荐

**社交功能**:
- 公开分享自选股分组
- 查看大V的自选股
- 自选股排行榜

---

## 附录

### A. 数据库迁移脚本位置

`sql/migrations/005_create_watchlist_tables.sql`

### B. API文档位置

`doc/api/watchlist_api.md` (待创建)

### C. 前端组件文档位置

`frontend/src/pages/Watchlist/README.md` (待创建)

### D. 参考资料

- AkShare文档: https://akshare.akfamily.xyz/
- 同花顺自选股: https://www.10jqka.com.cn/
- 雪球组合: https://xueqiu.com/

### E. 相关Issue跟踪

- GitHub Issue #XXX: 自选股功能开发跟踪
- GitHub Issue #YYY: 实时行情性能优化

---

**文档维护**:
- 创建: 2025-11-19
- 负责人: TBD
- 审核: TBD
- 下次评审: 实施前

**变更记录**:
| 日期 | 版本 | 变更内容 | 修改人 |
|------|------|----------|--------|
| 2025-11-19 | v1.0 | 初始版本 | - |
