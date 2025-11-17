# 策略文档展示功能 - 开发计划

**创建时间**: 2025-11-10
**状态**: 进行中

---

## 📋 总体目标
在回测页面中，为每个策略添加"查看详情"功能，通过Modal弹窗展示完整的Markdown格式策略文档。

---

## 🎯 Phase 1: 基础功能实现（MVP）

### 任务1: 后端 - 添加策略文档API接口
**目标**: 提供获取策略Markdown文档的API
- [ ] 在 `backend/app/api/v1/` 创建或扩展策略API
- [ ] 添加 `GET /api/v1/strategies/{strategy_id}/documentation` 端点
- [ ] 读取 `doc/strategy/{strategy_id}.md` 文件并返回内容
- [ ] 处理文件不存在的情况（返回404或默认文档）
- [ ] 测试API端点

### 任务2: 前端 - 安装Markdown渲染依赖
**目标**: 安装必要的npm包
- [ ] 安装 `react-markdown`（Markdown渲染）
- [ ] 安装 `remark-gfm`（支持GitHub风格Markdown）
- [ ] 安装 `react-syntax-highlighter`（代码高亮，可选）
- [ ] 验证安装成功

### 任务3: 前端 - 创建StrategyDocModal组件
**目标**: 创建专门的策略文档弹窗组件
- [ ] 创建 `frontend/src/components/StrategyDocModal.tsx`
- [ ] 实现基础Modal结构（使用Ant Design Modal）
- [ ] 集成react-markdown渲染器
- [ ] 添加加载状态（Spin）
- [ ] 添加错误处理（文档加载失败）
- [ ] 样式优化（让Markdown渲染更美观）

### 任务4: 前端 - 扩展API服务
**目标**: 添加获取策略文档的API调用
- [ ] 在 `frontend/src/services/api.ts` 中添加 `getStrategyDocumentation` 方法
- [ ] 添加TypeScript类型定义

### 任务5: 前端 - 集成到BacktestPage
**目标**: 在回测页面中添加"查看详情"功能
- [ ] 在策略卡片添加"查看详情"图标/按钮
- [ ] 添加Modal状态管理（打开/关闭）
- [ ] 点击按钮时调用API获取文档
- [ ] 将文档内容传递给StrategyDocModal
- [ ] 测试交互流程

### 任务6: 测试与优化
**目标**: 确保功能正常工作
- [ ] 测试所有策略的文档加载
- [ ] 测试Modal的打开/关闭
- [ ] 测试响应式布局（手机、平板、桌面）
- [ ] 优化Markdown样式（标题、表格、列表等）
- [ ] 处理边界情况（文档不存在、网络错误等）

---

## 🚀 Phase 2: 增强功能（可选，后续实现）

### 任务7: 添加目录导航（TOC）
- [ ] 解析Markdown生成目录
- [ ] 在Modal左侧显示目录
- [ ] 实现点击跳转到对应章节
- [ ] 高亮当前阅读位置

### 任务8: 策略间快速切换
- [ ] 在Modal底部添加"上一个/下一个策略"按钮
- [ ] 实现策略文档的切换逻辑
- [ ] 保持Modal打开状态

### 任务9: 文档内搜索
- [ ] 在Modal顶部添加搜索框
- [ ] 实现关键词高亮
- [ ] 显示搜索结果数量

---

## 📁 预计修改的文件

### 后端
1. `backend/app/api/v1/strategies.py` - 添加文档API
2. 可能需要新建 `backend/app/api/v1/documentation.py`

### 前端
1. `frontend/src/components/StrategyDocModal.tsx` - 新建
2. `frontend/src/pages/BacktestPage.tsx` - 修改
3. `frontend/src/services/api.ts` - 修改
4. `frontend/src/types/index.ts` - 修改（添加类型）
5. `frontend/package.json` - 修改（添加依赖）

---

## ⏱️ 预计时间
- **Phase 1 (MVP)**: 约2-3小时
- **Phase 2 (增强)**: 约2-3小时

---

## 🔍 技术细节

### Markdown渲染配置
```tsx
<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  components={{
    // 自定义样式
    h1: ({node, ...props}) => <h1 style={{...}} {...props} />,
    h2: ({node, ...props}) => <h2 style={{...}} {...props} />,
    table: ({node, ...props}) => <table className="markdown-table" {...props} />,
    // ... 更多自定义
  }}
>
  {markdownContent}
</ReactMarkdown>
```

### API响应格式
```typescript
GET /api/v1/strategies/{strategy_id}/documentation

Response:
{
  "strategy_id": "ma_cross",
  "strategy_name": "均线金叉",
  "content": "# MA Cross 策略文档\n\n...",
  "last_updated": "2025-11-10"
}
```

---

## 📝 实施记录

### 2025-11-10
- ✅ 创建开发计划文档
- ✅ 后端 - 添加策略文档API接口
  - 创建 `StrategyDocumentationResource` 类
  - 注册路由 `/api/v1/strategies/<strategy_id>/documentation`
  - 读取 `doc/strategy/{strategy_id}.md` 文件
  - 在 docker-compose.yml 中挂载 `./doc:/app/doc`
  - 重新构建后端镜像
- ✅ 前端 - 安装Markdown渲染依赖
  - 安装 `react-markdown` 和 `remark-gfm`
- ✅ 前端 - 创建StrategyDocModal组件
  - 创建 Modal 组件展示策略文档
  - 集成 ReactMarkdown 渲染器
  - 自定义 Markdown 样式（标题、表格、列表、代码等）
  - 添加加载状态和错误处理
- ✅ 前端 - 扩展API服务
  - 添加 `StrategyDocumentation` 类型定义
  - 在 `strategyApi` 中添加 `getStrategyDocumentation` 方法
- ✅ 前端 - 集成到BacktestPage
  - 在策略卡片添加"查看详情"图标按钮
  - 添加 Modal 状态管理
  - 实现点击按钮打开 Modal 展示文档
  - 重新构建前端镜像
- ✅ 测试与优化
  - 测试后端API正常返回文档内容
  - 验证前端Modal正确显示
  - 所有6个策略文档都可正常加载

---

## 🐛 遇到的问题和解决方案

### 问题1: 后端代码更新后容器重启无效
**问题**: 修改后端代码后，仅重启容器无法加载新代码，API返回404。
**原因**: Docker容器没有挂载代码目录，代码是在镜像构建时复制进去的。
**解决**: 重新构建后端镜像 `docker-compose build backend`，然后重启容器。

### 问题2: 找不到策略文档文件
**问题**: API路由正常，但返回 "Documentation not found"。
**原因**: `doc/` 目录在项目根目录，但容器内没有该目录。
**解决**: 在 `docker-compose.yml` 中添加卷挂载：`./doc:/app/doc`。

---

## ✅ 验收标准

Phase 1完成标准：
- ✅ 用户可以在策略卡片上看到"查看详情"按钮
- ✅ 点击按钮后打开Modal弹窗
- ✅ Modal中正确渲染Markdown格式的策略文档
- ✅ 文档包含完整内容：标题、表格、列表、代码块等
- ✅ 样式美观，易于阅读
- ✅ 支持关闭Modal
- ✅ 所有策略都能正确加载文档
- ✅ 错误情况有合理提示

**Phase 1 已完成！** 🎉
