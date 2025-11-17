# 精简账户认证系统 - 设计文档

**版本**: v1.0
**创建时间**: 2025-11-17
**状态**: 设计中
**关联文档**:
- Backlog: `doc/backlog/用户账户系统.md`
- 数据库表: `sql/modules/03_user_management.sql`

---

## 1. 概述

### 1.1 目的

为 Stock Pal 实现最精简的用户认证系统,支持基于用户 ID 的功能开发(如配置保存、回测历史等),同时避免复杂的注册流程和账户管理功能。

### 1.2 目标

- ✅ 支持用户名/密码登录
- ✅ JWT Token 认证机制
- ✅ 用户信息查询接口
- ✅ 前端登录页面和状态管理
- ✅ 预置测试账号(通过数据库初始化脚本)
- ✅ 为后续功能提供 user_id 关联能力

### 1.3 非目标

- ❌ 用户注册功能
- ❌ 找回密码
- ❌ 邮箱/手机验证
- ❌ 第三方登录
- ❌ 多设备管理
- ❌ 用户资料编辑
- ❌ 权限角色管理(暂时不区分普通用户/管理员)

### 1.4 设计原则

**极简主义**: 只实现最核心的认证流程,避免过度设计
**数据库优先**: 用户数据存储在数据库中,为后续功能提供真实的 user_id
**易扩展**: 预留扩展接口,未来可平滑升级到完整账户系统

---

## 2. 背景

### 2.1 当前状态

- 系统目前没有任何认证机制
- 所有 API 接口无需登录即可访问
- 无法实现配置保存、回测历史等需要用户身份的功能
- 数据库表 `users` 已定义但未启用

### 2.2 为什么需要精简版本

**项目处于早期阶段**:
- 用户基数小,可通过配置文件预置账号
- 避免开发注册、验证等复杂流程
- 快速实现 MVP,验证核心价值

**开发效率**:
- 减少开发时间(2-3天 vs 2-3周)
- 降低测试复杂度
- 专注于核心回测功能

**未来可扩展**:
- 数据结构保持完整,只是关闭了注册入口
- 需要时只需添加注册 API,无需重构

---

## 3. 架构设计

### 3.1 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  LoginPage   │→ │ AuthContext  │→ │ API Clients  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────────────────┼────────────────────────┘
                                 │ HTTP + JWT Token
                                 ↓
┌─────────────────────────────────────────────────────────┐
│                      Backend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Auth API    │→ │ AuthService  │→ │  Database    │ │
│  │  (v1/auth)   │  │  (verify)    │  │   (users)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↑                                               │
│         │ @jwt_required decorator                      │
│         ↓                                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Protected APIs (backtest, configs, etc.)        │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3.2 认证流程

#### 登录流程

```
User                Frontend            Backend             Database
 │                      │                   │                   │
 │  输入用户名/密码     │                   │                   │
 ├─────────────────────>│                   │                   │
 │                      │  POST /auth/login │                   │
 │                      ├──────────────────>│                   │
 │                      │                   │  查询用户         │
 │                      │                   ├──────────────────>│
 │                      │                   │  用户信息+密码hash│
 │                      │                   │<──────────────────┤
 │                      │                   │                   │
 │                      │                   │  验证密码         │
 │                      │                   │  (bcrypt.verify)  │
 │                      │                   │                   │
 │                      │  JWT Token        │                   │
 │                      │<──────────────────┤                   │
 │                      │                   │                   │
 │                      │ 存储到 localStorage                  │
 │                      │                   │                   │
 │  登录成功            │                   │                   │
 │<─────────────────────┤                   │                   │
```

#### 访问受保护资源

```
Frontend            Backend             Database
   │                   │                   │
   │  GET /api/v1/xxx  │                   │
   │  Header:          │                   │
   │  Authorization:   │                   │
   │  Bearer <token>   │                   │
   ├──────────────────>│                   │
   │                   │                   │
   │                   │  验证 JWT Token   │
   │                   │  (签名+过期时间)  │
   │                   │                   │
   │                   │  解析 user_id     │
   │                   │                   │
   │                   │  查询用户信息     │
   │                   ├──────────────────>│
   │                   │<──────────────────┤
   │                   │                   │
   │  返回数据         │                   │
   │<──────────────────┤                   │
```

---

## 4. API 设计

### 4.1 认证接口

#### POST /api/v1/auth/login

**功能**: 用户登录

**请求**:
```json
{
  "username": "test",
  "password": "test123"
}
```

**响应 (成功)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "test",
    "nickname": "测试用户",
    "email": "test@stockpal.com"
  }
}
```

**响应 (失败)**:
```json
{
  "error": "invalid_credentials",
  "message": "用户名或密码错误"
}
```

**状态码**:
- `200 OK`: 登录成功
- `401 Unauthorized`: 用户名或密码错误
- `400 Bad Request`: 请求参数错误

---

#### GET /api/v1/auth/me

**功能**: 获取当前用户信息

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "test",
  "nickname": "测试用户",
  "email": "test@stockpal.com",
  "created_at": "2025-11-17T10:00:00Z",
  "last_login_at": "2025-11-17T14:30:00Z"
}
```

**状态码**:
- `200 OK`: 成功
- `401 Unauthorized`: Token 无效或过期

---

#### POST /api/v1/auth/logout (可选)

**功能**: 登出(客户端删除 Token 即可,服务端可选实现黑名单)

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "message": "成功登出"
}
```

---

### 4.2 受保护接口示例

未来所有需要用户身份的接口都需要添加 JWT 认证:

```
GET    /api/v1/backtest/history    # 获取用户的回测历史
POST   /api/v1/configs              # 保存用户配置
GET    /api/v1/configs              # 获取用户配置列表
DELETE /api/v1/configs/{id}         # 删除用户配置
```

---

## 5. 数据模型

### 5.1 数据库表

#### users 表 (简化版)

基于现有的 `sql/modules/03_user_management.sql`,只启用核心字段:

| 字段 | 类型 | 说明 | 必填 | 默认值 |
|------|------|------|------|--------|
| `id` | VARCHAR(36) | 用户 ID (UUID) | ✅ | uuid_generate_v4() |
| `username` | VARCHAR(50) | 用户名 | ✅ | - |
| `email` | VARCHAR(100) | 邮箱 | ✅ | - |
| `password_hash` | VARCHAR(255) | 密码哈希 (bcrypt) | ✅ | - |
| `nickname` | VARCHAR(50) | 昵称 | ❌ | NULL |
| `is_active` | BOOLEAN | 是否激活 | ✅ | TRUE |
| `created_at` | TIMESTAMP | 创建时间 | ✅ | CURRENT_TIMESTAMP |
| `last_login_at` | TIMESTAMP | 最后登录时间 | ❌ | NULL |

**未使用字段** (预留):
- `avatar_url`: 头像
- `is_verified`: 邮箱验证
- `is_premium`: 付费用户
- `role`: 角色
- `salt`: 盐值 (bcrypt 内置)

**索引**:
- 主键: `id`
- 唯一索引: `username`, `email`

### 5.2 初始数据

创建文件 `sql/mock_data/initial_users.sql`:

| username | password | nickname | email | 用途 |
|----------|----------|----------|-------|------|
| admin | admin123 | 管理员 | admin@stockpal.com | 管理员账号 |
| test | test123 | 测试用户 | test@stockpal.com | 测试账号 |
| demo | demo123 | 演示账号 | demo@stockpal.com | 演示账号 |

**密码哈希**: 使用 bcrypt (cost factor = 12)

---

## 6. 前端设计

### 6.1 页面结构

```
src/
├── pages/
│   └── LoginPage.tsx          # 新增: 登录页面
├── contexts/
│   └── AuthContext.tsx        # 新增: 认证上下文
├── utils/
│   └── auth.ts                # 新增: Token 管理工具
└── components/
    └── PrivateRoute.tsx       # 新增: 路由守卫
```

### 6.2 路由配置

```
/                     # 首页 (公开)
/login                # 登录页 (公开)
/backtest             # 回测页面 (需登录)
/configs              # 配置管理 (需登录) - 未来功能
/profile              # 个人中心 (需登录) - 未来功能
```

### 6.3 状态管理

**AuthContext** 提供:
```typescript
interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}
```

### 6.4 Token 管理

**存储位置**: `localStorage.getItem('auth_token')`

**Token 刷新**: 初期不实现刷新机制,Token 有效期设为 24 小时

**自动注入**: axios 拦截器自动添加 `Authorization` 头

---

## 7. 安全设计

### 7.1 密码安全

- **哈希算法**: bcrypt (cost factor = 12)
- **不存储明文**: 数据库只存储 `password_hash`
- **盐值**: bcrypt 自动生成和管理

### 7.2 JWT 安全

- **签名算法**: HS256 (HMAC-SHA256)
- **Secret Key**: 通过环境变量配置,不硬编码
- **Token 有效期**: 24 小时
- **Payload 内容**: 只包含 `user_id` 和 `exp`,不包含敏感信息

示例 Payload:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "exp": 1700236800
}
```

### 7.3 API 安全

- **HTTPS**: 生产环境强制使用 HTTPS
- **CORS**: 限制允许的域名
- **Rate Limiting**: 登录接口限流 (5次/分钟) - 未来增强
- **防止暴力破解**: 暂不实现锁定机制 (精简版)

---

## 8. 实施计划

### Phase 1: 数据库和后端认证 (Day 1)

**任务**:
1. 生成测试用户的 bcrypt 密码哈希
2. 创建 `sql/mock_data/initial_users.sql`
3. 修改 `sql/init_stock_db.sql`,启用 mock 数据导入
4. 添加 Python 依赖: `flask-jwt-extended`, `bcrypt`
5. 实现 `app/services/auth_service.py`
6. 实现 `app/api/v1/auth.py`
7. 创建 JWT 装饰器 `@jwt_required`
8. 编写单元测试

**验收标准**:
- [ ] 数据库初始化脚本能创建测试用户
- [ ] POST /api/v1/auth/login 返回 JWT Token
- [ ] GET /api/v1/auth/me 返回用户信息
- [ ] 无效 Token 返回 401 错误

---

### Phase 2: 前端登录页面 (Day 2)

**任务**:
1. 创建 LoginPage 组件
2. 实现 AuthContext
3. 实现 auth.ts 工具函数
4. 配置 axios 拦截器
5. 创建 PrivateRoute 组件
6. 更新路由配置

**验收标准**:
- [ ] 登录页面 UI 正常显示
- [ ] 输入正确账号密码能登录成功
- [ ] Token 存储到 localStorage
- [ ] 未登录访问 /backtest 跳转到 /login
- [ ] 登录后 Header 显示用户昵称

---

### Phase 3: 集成和测试 (Day 3)

**任务**:
1. 端到端测试登录流程
2. 测试 Token 过期处理
3. 测试退出登录
4. 更新回测接口,关联 user_id (可选)
5. 文档更新

**验收标准**:
- [ ] 完整登录流程测试通过
- [ ] Token 过期后自动跳转登录页
- [ ] 退出登录清除 Token
- [ ] 所有受保护接口需要 Token

---

## 9. 测试策略

### 9.1 后端单元测试

**AuthService**:
- `test_verify_password_success`: 正确密码验证成功
- `test_verify_password_failure`: 错误密码验证失败
- `test_authenticate_user_success`: 用户认证成功
- `test_authenticate_user_invalid_username`: 无效用户名
- `test_authenticate_user_invalid_password`: 无效密码

**Auth API**:
- `test_login_success`: 登录成功返回 Token
- `test_login_invalid_credentials`: 登录失败返回 401
- `test_get_me_success`: 有效 Token 返回用户信息
- `test_get_me_no_token`: 无 Token 返回 401
- `test_get_me_invalid_token`: 无效 Token 返回 401

### 9.2 前端测试

**手动测试场景**:
1. 登录成功场景
2. 登录失败场景 (错误密码)
3. 未登录访问受保护页面
4. Token 过期后访问
5. 退出登录

### 9.3 集成测试

- 完整登录流程
- Token 携带到受保护接口
- Token 过期自动跳转

---

## 10. 替代方案

### 方案 A: 配置文件存储用户

**优点**:
- 无需数据库查询,性能更好
- 实现更简单

**缺点**:
- 无法关联 user_id 到其他表 (致命缺陷)
- 无法记录登录时间等信息
- 扩展性差

**决策**: ❌ 拒绝 - 无法满足后续功能开发需求

---

### 方案 B: Session-based 认证

**优点**:
- 传统方案,成熟稳定
- 易于撤销会话

**缺点**:
- 需要 Redis/数据库存储 Session
- 无状态扩展性差
- 移动端支持不佳

**决策**: ❌ 拒绝 - JWT 更适合前后端分离架构

---

### 方案 C: OAuth2 / OpenID Connect

**优点**:
- 标准化协议
- 支持第三方登录

**缺点**:
- 过度设计,复杂度高
- 需要额外的授权服务器

**决策**: ❌ 拒绝 - 当前阶段不需要

---

## 11. 未来扩展

### 11.1 迁移到完整账户系统

需要添加的功能:
1. **注册接口**: POST /api/v1/auth/register
2. **找回密码**: 邮箱验证码
3. **用户资料编辑**: PUT /api/v1/users/me
4. **头像上传**: POST /api/v1/users/me/avatar
5. **多设备管理**: user_sessions 表

**数据结构不变**: 只需添加 API,无需重构

### 11.2 增强安全性

1. **Token 刷新机制**: Refresh Token (7 天) + Access Token (1 小时)
2. **登录限流**: 防止暴力破解
3. **Token 黑名单**: 使用 Redis 存储已撤销的 Token
4. **登录历史**: 记录 IP、设备、登录时间

---

## 12. 风险与注意事项

### 12.1 安全风险

**风险**: JWT Secret Key 泄露

**对策**:
- Secret Key 通过环境变量配置
- 生产环境使用强随机字符串 (至少 32 字节)
- 不提交到代码仓库

---

**风险**: Token 无法主动撤销

**对策**:
- Token 有效期设置为 24 小时
- 未来实现 Token 黑名单

---

### 12.2 开发风险

**风险**: Docker 容器重启后用户数据丢失

**对策**:
- 确保 PostgreSQL 数据持久化 (Docker volume)
- 初始化脚本使用 `IF NOT EXISTS` 避免重复创建

---

### 12.3 用户体验

**风险**: Token 过期后体验不佳

**对策**:
- 前端检测 401 错误自动跳转登录页
- 显示友好的错误提示
- 未来实现 Token 自动刷新

---

## 13. 配置说明

### 13.1 后端配置

在 `backend/app/config.py` 添加:

```python
# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
```

**环境变量**:
- `JWT_SECRET_KEY`: JWT 签名密钥 (生产环境必须配置)
- `JWT_ACCESS_TOKEN_EXPIRES`: Token 有效期 (默认 24 小时)

### 13.2 前端配置

在 `frontend/src/config.ts` 添加:

```typescript
export const AUTH_TOKEN_KEY = 'auth_token';
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:4001';
```

---

## 14. 相关文档

- **Backlog**: `doc/backlog/用户账户系统.md` (完整账户系统规划)
- **数据库表**: `sql/modules/03_user_management.sql`
- **API 文档**: 待创建 `doc/api/auth_api.md`

---

## 15. 开放问题

- [ ] Token 有效期设置为 24 小时是否合理?
- [ ] 是否需要"记住我"功能 (延长 Token 有效期)?
- [ ] 是否需要在前端显示 Token 剩余时间?
- [ ] 回测接口是否需要立即关联 user_id? (建议暂不关联,保持向后兼容)

---

**文档状态**: ✅ 设计完成
**下一步**: 开始实施 Phase 1
