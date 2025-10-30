# Frontend - 股票回测系统前端

基于React + TypeScript的现代化前端应用。

## 技术栈

- React 18
- TypeScript
- Ant Design 5
- ECharts 5
- Vite
- Axios

## 安装

```bash
npm install
```

## 运行

```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview

# 代码检查
npm run lint
```

## 项目结构

```
frontend/
├── src/
│   ├── pages/              # 页面组件
│   │   ├── HomePage.tsx       # 首页
│   │   └── BacktestPage.tsx   # 回测页面
│   ├── components/         # 通用组件
│   │   ├── KLineChart.tsx         # K线图
│   │   └── EquityCurveChart.tsx   # 资产曲线图
│   ├── services/           # API服务
│   │   └── api.ts
│   ├── types/              # TypeScript类型定义
│   │   └── index.ts
│   ├── utils/              # 工具函数
│   │   └── format.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 环境变量

创建 `.env.development` 文件：

```
VITE_API_BASE_URL=http://localhost:5000
```

## 开发说明

### 添加新页面

1. 在 `src/pages/` 创建新组件
2. 在 `App.tsx` 中添加路由
3. 更新导航菜单

### 添加新图表

1. 在 `src/components/` 创建图表组件
2. 使用 ECharts 进行数据可视化
3. 确保响应式设计

### API调用

所有API调用都通过 `src/services/api.ts` 进行：

```typescript
import { backtestApi } from '@/services/api';

const result = await backtestApi.runBacktest({
  symbol: '000001',
  strategy_id: 'ma_cross',
  // ...
});
```
