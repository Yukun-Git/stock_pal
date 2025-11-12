import { Typography, Row, Col } from 'antd';
import type { StrategyAnalysis } from '@/types';
import { getStatusConfig, getProximityConfig } from './analysisConfig';

const { Text } = Typography;

interface StrategyAnalysisItemProps {
  analysis: StrategyAnalysis;
}

/**
 * StrategyAnalysisItem - Renders a single strategy's signal analysis
 *
 * This component uses configuration-driven rendering instead of hardcoded
 * if-else logic for status colors, icons, and proximity badges.
 *
 * Before refactoring (hardcoded in BacktestPage):
 * - 104 lines of hardcoded status and proximity logic
 * - Colors and icons determined by if-else chains
 * - Difficult to add new status types or customize styling
 *
 * After refactoring:
 * - Configuration-driven rendering via analysisConfig
 * - Easy to add new status types or proximity levels
 * - Reusable component with single responsibility
 */
export default function StrategyAnalysisItem({ analysis }: StrategyAnalysisItemProps) {
  // Use configuration-driven styling (no hardcoded if-else!)
  const statusConfig = getStatusConfig(analysis.status);
  const proximityConfig = getProximityConfig(analysis.proximity);

  return (
    <div
      style={{
        padding: 16,
        backgroundColor: '#fafafa',
        borderRadius: 8,
        borderLeft: `4px solid ${statusConfig.color}`,
      }}
    >
      {/* Strategy Name with Status Icon */}
      <div style={{ marginBottom: 12 }}>
        <Text strong style={{ fontSize: 15, color: statusConfig.color }}>
          {statusConfig.icon} {analysis.strategy_name}
        </Text>
        {proximityConfig && (
          <span
            style={{
              marginLeft: 8,
              padding: '2px 8px',
              backgroundColor: proximityConfig.badge.bgColor,
              color: proximityConfig.badge.textColor,
              borderRadius: 4,
              fontSize: 12,
              fontWeight: proximityConfig.badge.fontWeight || 'normal',
            }}
          >
            {proximityConfig.badge.emoji && `${proximityConfig.badge.emoji} `}
            {proximityConfig.badge.text}
          </span>
        )}
      </div>

      {/* Indicators */}
      {analysis.indicators && Object.keys(analysis.indicators).length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <Row gutter={[16, 8]}>
            {Object.entries(analysis.indicators).map(([key, value]) => (
              <Col key={key} xs={12} sm={8} md={6}>
                <div
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#fff',
                    borderRadius: 4,
                    border: '1px solid #e8e8e8',
                  }}
                >
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {key}:
                  </Text>
                  <br />
                  <Text strong style={{ fontSize: 13 }}>
                    {value}
                  </Text>
                </div>
              </Col>
            ))}
          </Row>
        </div>
      )}

      {/* Current State */}
      <div style={{ marginBottom: 8 }}>
        <Text style={{ fontSize: 13 }}>
          📍 <Text strong>当前状态：</Text>
          {analysis.current_state}
        </Text>
      </div>

      {/* Proximity Description */}
      <div style={{ marginBottom: 8 }}>
        <Text style={{ fontSize: 13 }}>
          📏 <Text strong>距离信号：</Text>
          {analysis.proximity_description}
        </Text>
      </div>

      {/* Suggestion */}
      <div
        style={{
          marginTop: 12,
          padding: 12,
          backgroundColor: '#e6f7ff',
          borderRadius: 6,
          borderLeft: '3px solid #1890ff',
        }}
      >
        <Text style={{ fontSize: 13, color: '#096dd9' }}>
          💡 <Text strong>操作建议：</Text>
          {analysis.suggestion}
        </Text>
      </div>
    </div>
  );
}
