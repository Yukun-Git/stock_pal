import { Card, Typography } from 'antd';
import { BulbOutlined } from '@ant-design/icons';
import type { SignalAnalysis } from '@/types';
import StrategyAnalysisItem from './StrategyAnalysisItem';

const { Text } = Typography;

interface SignalAnalysisCardProps {
  signalAnalysis: SignalAnalysis;
}

/**
 * SignalAnalysisCard - Main card component for displaying signal analysis
 *
 * This component replaces 104 lines of hardcoded rendering logic in BacktestPage
 * with a clean, reusable component.
 *
 * Before refactoring (BacktestPage.tsx: 769-892):
 * - 104 lines of inline rendering logic
 * - Hardcoded status colors and proximity badges
 * - Difficult to maintain and extend
 *
 * After refactoring:
 * - 1 line in BacktestPage: <SignalAnalysisCard signalAnalysis={result.signal_analysis} />
 * - Configuration-driven styling
 * - Easy to customize and extend
 */
export default function SignalAnalysisCard({ signalAnalysis }: SignalAnalysisCardProps) {
  // Don't render if no analyses available
  if (!signalAnalysis.analyses || signalAnalysis.analyses.length === 0) {
    return null;
  }

  return (
    <Card
      title={
        <span>
          <BulbOutlined style={{ marginRight: 8, color: '#faad14' }} />
          当前信号分析
        </span>
      }
      style={{ marginTop: 24 }}
    >
      {/* Analysis Date and Price Info */}
      <div style={{ marginBottom: 16 }}>
        <Text type="secondary">
          基于 <Text strong>{signalAnalysis.date}</Text> 的数据
          （收盘价：
          <Text strong style={{ color: '#1890ff' }}>
            ¥{signalAnalysis.close_price.toFixed(2)}
          </Text>
          ）
        </Text>
      </div>

      {/* Strategy Analyses */}
      {signalAnalysis.analyses.map((analysis, index) => (
        <div
          key={analysis.strategy_id}
          style={{
            marginBottom: index < signalAnalysis.analyses.length - 1 ? 20 : 0,
          }}
        >
          <StrategyAnalysisItem analysis={analysis} />
        </div>
      ))}
    </Card>
  );
}
