# Agent 使用指南

本目录包含 Stock Pal 项目的专业 Agent 定义文件。

## 📋 可用 Agent

### req-writer - 需求文档专家

**职责**：编写和管理需求文档（头脑风暴、Backlog）

**何时使用**：
- 有新的功能想法需要整理成文档
- 需要进行头脑风暴分析
- 需要创建正式的 Backlog 需求文档
- 需要更新已有的需求文档

**启动方式**：
```bash
# 调用 agent
用户: 我想写一个关于止损功能的需求文档
用户: 帮我整理一下市场分析的头脑风暴
用户: 创建XXX功能的 Backlog 文档
```

**输入**：
- 功能想法和描述
- 用户场景和需求点
- 功能的核心价值

**输出**：
- 头脑风暴文档（`doc/brainstorm/`）
- Backlog 需求文档（`doc/backlog/`）
- 更新的 `doc/backlog/README.md`
- 更新的文档索引（通过 doc-manager）

**核心原则**：
- ✅ 专注需求本身，描述"做什么"和"为什么"
- ⚠️ 只在必要时包含少量概念性设计
- ❌ 绝不包含代码实现细节
- 🔍 编写前查找相关文档，避免重复
- 📋 编写后自动更新文档索引

**不适用于**：
- 编写技术设计文档（应该由设计 agent 负责）
- 编写代码实现
- 编写测试用例

---

### doc-manager - 文档管理专家

**职责**：管理 `doc/` 目录下的所有文档，维护文档索引

**何时使用**：
- 需要查找某个主题的相关文档
- 创建了新文档，需要注册到索引
- 想了解文档统计信息
- 需要刷新文档索引

**启动方式**：
```bash
# 调用 agent（通过 SlashCommand tool）
/doc-manager                    # 查看状态和可用操作
/doc-manager index              # 创建/更新文档索引
/doc-manager find <主题>        # 查找相关文档
/doc-manager add <文件路径>     # 注册新文档
/doc-manager stats              # 查看文档统计
```

**输入**：
- 主题关键词（查找文档时）
- 文件路径（注册新文档时）

**输出**：
- 更新的 `doc/DOC_INDEX.md`
- 文档搜索结果列表
- 文档统计报告

**不适用于**：
- 编写文档内容（设计文档、需求文档等）
- 代码开发或测试
- 修改已有文档内容（除了 DOC_INDEX.md）

---

## 🔧 如何使用 Agent

### 方法 1: 直接调用（推荐）

在对话中直接使用 agent 名称：

```
用户: /doc-manager find 回测引擎
```

### 方法 2: 自然语言触发

Agent 会根据描述中的触发词自动启动：

```
用户: 帮我查找关于风险管理的文档
→ doc-manager agent 自动启动
```

### 方法 3: 其他 Agent 调用

其他 agent 可以通过 SlashCommand tool 调用 doc-manager：

```python
# 伪代码示例
SlashCommand(command="/doc-manager find 回测")
```

---

## 📂 文档目录结构

```
doc/
├── api/              # API 使用文档和示例
├── backlog/          # 功能需求 backlog（未来开发）
├── brainstorm/       # 头脑风暴和分析文档
├── design/           # 功能设计文档
│   └── done/         # 已完成的设计文档
├── development/      # 开发进度跟踪
│   ├── done/         # 已完成的开发总结
│   └── progress/     # 进行中的开发进度
├── plan/             # 项目规划文档
├── requirements/     # 产品需求和路线图
├── strategy/         # 交易策略文档
├── strategy_params/  # 策略参数文档
└── DOC_INDEX.md      # 文档索引（由 doc-manager 维护）
```

---

## 🚀 快速开始

### 1. 初次使用：创建文档索引

```bash
用户: /doc-manager index
```

这将扫描所有 `doc/` 下的 markdown 文件并创建索引。

### 2. 查找文档

```bash
用户: /doc-manager find 回测
用户: /doc-manager find KDJ 策略
用户: /doc-manager find risk management
```

### 3. 创建新文档后注册

```bash
# 假设你刚创建了一个新的设计文档
用户: /doc-manager add doc/design/new_feature_design.md
```

### 4. 查看文档统计

```bash
用户: /doc-manager stats
```

---

## 🔄 工作流示例

### 场景 1: 从想法到 Backlog（req-writer + doc-manager 协作）

```
1. 用户: "我想加一个止损功能"
2. req-writer: 启动，询问详细需求
3. req-writer: 内部调用 /doc-manager find 止损
4. doc-manager: 返回查找结果（如果有相关文档）
5. req-writer: 基于查找结果，决定创建新文档或更新已有文档
6. req-writer: 收集用户需求，编写 Backlog 文档
7. req-writer: 保存 doc/backlog/stop_loss.md
8. req-writer: 调用 /doc-manager add doc/backlog/stop_loss.md
9. doc-manager: 更新 DOC_INDEX.md
10. req-writer: 确认完成，提示下一步建议
```

### 场景 2: 头脑风暴到多个 Backlog

```
1. 用户: "帮我分析一下完整的风控系统需要哪些模块"
2. req-writer: 创建头脑风暴文档 doc/brainstorm/risk_control_analysis.md
3. req-writer: 分析识别出 3 个核心模块
4. 用户: "好的，把这些整理成 Backlog"
5. req-writer: 逐个创建 Backlog 文档
6. req-writer: 每创建一个就调用 doc-manager 更新索引
7. req-writer: 更新 doc/backlog/README.md 添加新条目
```

### 场景 3: 查找文档开始开发

```
1. 用户: "我要开发回测引擎的改进，先看看有没有相关文档"
2. doc-manager: 查找 "回测引擎" 相关文档
3. doc-manager: 返回相关设计文档、需求文档、API 文档列表
4. 用户: 阅读相关文档后开始开发
```

### 场景 4: 定期维护

```
1. 用户: /doc-manager stats
2. doc-manager: 显示统计，发现最近有 5 个新文档
3. 用户: /doc-manager index
4. doc-manager: 刷新索引，包含所有新文档
```

---

## 📝 最佳实践

### ✅ 推荐做法

1. **定期刷新索引**
   - 每周或在创建多个新文档后运行 `/doc-manager index`
   - 确保索引包含最新文档

2. **新文档立即注册**
   - 创建重要文档后立即运行 `/doc-manager add`
   - 方便其他人和 agent 查找

3. **使用查找功能**
   - 在查看代码或开发新功能前，先用 `/doc-manager find` 查找相关文档
   - 避免重复造轮子

4. **利用统计信息**
   - 定期查看 `/doc-manager stats` 了解文档健康度
   - 跟进 progress/ 下的进行中文档

### ❌ 避免的做法

1. **不要手动编辑 DOC_INDEX.md**
   - 总是通过 doc-manager 更新索引
   - 保持格式一致性

2. **不要依赖记忆**
   - 不要试图记住所有文档路径
   - 使用 doc-manager 查找

3. **不要忽略索引过期**
   - 如果索引很久没更新，及时刷新
   - 过期索引会导致查找不到新文档

---

## 🔮 未来 Agent 规划

随着项目发展，可能会添加以下 agent：

- **design-planner** - 技术设计专家（基于 Backlog 生成技术设计文档）
- **strategy-writer** - 交易策略文档编写专家
- **dev-tracker** - 开发进度跟踪专家
- **test-designer** - 测试用例设计专家
- **code-reviewer** - 代码审查专家

### Agent 协作流程（完整生命周期）

```
需求阶段:
  req-writer → 创建 Backlog 文档
      ↓
  doc-manager → 更新文档索引
      ↓

设计阶段:
  design-planner → 基于 Backlog 创建设计文档
      ↓
  doc-manager → 更新索引
      ↓

开发阶段:
  开发者/AI → 实现功能
      ↓
  code-reviewer → 审查代码
      ↓

测试阶段:
  test-designer → 设计测试用例
      ↓
  开发者/AI → 编写测试
      ↓

交付阶段:
  dev-tracker → 记录开发进度
      ↓
  doc-manager → 更新文档状态
```

每个 agent 都会与 doc-manager 协作，利用文档索引快速定位相关资料。

---

## 📚 参考资料

- [CLAUDE.md](../CLAUDE.md) - 项目总体指南
- [doc/DOC_INDEX.md](../doc/DOC_INDEX.md) - 文档索引（由 doc-manager 维护）

---

## 💡 提示

- Agent 文件是 markdown 格式，包含 YAML front matter
- 可以随时编辑 agent 文件来调整其行为
- Agent 之间可以相互调用，形成协作工作流

**享受高效的文档管理！** 🚀
