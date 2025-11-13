import { Drawer, Table, Typography, Divider, Row, Col, Statistic, Timeline, Tag } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import type { BacktestResult, RiskEvent } from '@/types';
import { formatPercent, formatCurrency } from '@/utils/format';

const { Title, Text } = Typography;

interface RiskComparisonDrawerProps {
  open: boolean;
  onClose: () => void;
  withRiskResult?: BacktestResult;
  withoutRiskResult?: BacktestResult;
  riskEvents?: RiskEvent[];
}

export default function RiskComparisonDrawer({
  open,
  onClose,
  withRiskResult,
  withoutRiskResult,
  riskEvents = [],
}: RiskComparisonDrawerProps) {
  if (!withRiskResult) {
    return null;
  }

  // 计算差异
  const calculateDiff = (withRisk: number, withoutRisk: number | undefined) => {
    if (withoutRisk === undefined) return null;
    const diff = withRisk - withoutRisk;
    return {
      value: diff,
      percent: withoutRisk !== 0 ? (diff / Math.abs(withoutRisk)) * 100 : 0,
      isPositive: diff >= 0,
    };
  };

  // 对比数据
  const comparisonData = [
    {
      key: 'total_return',
      metric: '总收益率',
      withoutRisk: withoutRiskResult ? formatPercent(withoutRiskResult.total_return) : '-',
      withRisk: formatPercent(withRiskResult.total_return),
      diff: calculateDiff(withRiskResult.total_return * 100, withoutRiskResult ? withoutRiskResult.total_return * 100 : undefined),
    },
    {
      key: 'cagr',
      metric: '年化收益率',
      withoutRisk: withoutRiskResult?.cagr ? formatPercent(withoutRiskResult.cagr) : '-',
      withRisk: withRiskResult.cagr ? formatPercent(withRiskResult.cagr) : '-',
      diff: calculateDiff((withRiskResult.cagr || 0) * 100, withoutRiskResult?.cagr ? withoutRiskResult.cagr * 100 : undefined),
    },
    {
      key: 'max_drawdown',
      metric: '最大回撤',
      withoutRisk: withoutRiskResult ? formatPercent(withoutRiskResult.max_drawdown) : '-',
      withRisk: formatPercent(withRiskResult.max_drawdown),
      diff: calculateDiff(withRiskResult.max_drawdown * 100, withoutRiskResult ? withoutRiskResult.max_drawdown * 100 : undefined),
      reverseColor: true, // 回撤是负向指标
    },
    {
      key: 'sharpe_ratio',
      metric: '夏普比率',
      withoutRisk: withoutRiskResult?.sharpe_ratio?.toFixed(2) || '-',
      withRisk: withRiskResult.sharpe_ratio?.toFixed(2) || '-',
      diff: calculateDiff(withRiskResult.sharpe_ratio || 0, withoutRiskResult?.sharpe_ratio),
    },
    {
      key: 'win_rate',
      metric: '胜率',
      withoutRisk: withoutRiskResult ? formatPercent(withoutRiskResult.win_rate) : '-',
      withRisk: formatPercent(withRiskResult.win_rate),
      diff: calculateDiff(withRiskResult.win_rate * 100, withoutRiskResult ? withoutRiskResult.win_rate * 100 : undefined),
    },
    {
      key: 'profit_factor',
      metric: '盈亏比',
      withoutRisk: withoutRiskResult?.profit_factor.toFixed(2) || '-',
      withRisk: withRiskResult.profit_factor.toFixed(2),
      diff: calculateDiff(withRiskResult.profit_factor, withoutRiskResult?.profit_factor),
    },
  ];

  const columns = [
    {
      title: '指标',
      dataIndex: 'metric',
      key: 'metric',
      width: '30%',
    },
    {
      title: '无风控',
      dataIndex: 'withoutRisk',
      key: 'withoutRisk',
      width: '25%',
      align: 'right' as const,
    },
    {
      title: '有风控',
      dataIndex: 'withRisk',
      key: 'withRisk',
      width: '25%',
      align: 'right' as const,
    },
    {
      title: '差异',
      dataIndex: 'diff',
      key: 'diff',
      width: '20%',
      align: 'right' as const,
      render: (diff: any, record: any) => {
        if (!diff) return '-';

        const isGood = record.reverseColor ? !diff.isPositive : diff.isPositive;
        const color = isGood ? '#52c41a' : '#ff4d4f';
        const icon = diff.isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />;

        return (
          <Text style={{ color }}>
            {icon} {diff.value >= 0 ? '+' : ''}{diff.value.toFixed(2)}%
          </Text>
        );
      },
    },
  ];

  // 按类型分组风控事件
  const groupedEvents = {
    stop_loss: riskEvents.filter(e => e.type === 'stop_loss'),
    stop_profit: riskEvents.filter(e => e.type === 'stop_profit'),
    drawdown_protection: riskEvents.filter(e => e.type === 'drawdown_protection'),
    rejected_order: riskEvents.filter(e => e.type === 'rejected_order'),
  };

  const renderEventTag = (type: string) => {
    const config: Record<string, { color: string; icon: string; label: string }> = {
      stop_loss: { color: 'orange', icon: '🛑', label: '止损' },
      stop_profit: { color: 'gold', icon: '💰', label: '止盈' },
      drawdown_protection: { color: 'red', icon: '⚠️', label: '回撤保护' },
      rejected_order: { color: 'default', icon: '🚫', label: '拒绝订单' },
    };
    const info = config[type] || config.rejected_order;
    return (
      <Tag color={info.color}>
        {info.icon} {info.label}
      </Tag>
    );
  };

  return (
    <Drawer
      title="风控对比分析"
      placement="right"
      onClose={onClose}
      open={open}
      width={720}
    >
      {/* 整体效果对比 */}
      <Title level={4}>📊 整体效果对比</Title>
      <Table
        dataSource={comparisonData}
        columns={columns}
        pagination={false}
        size="small"
        style={{ marginBottom: 24 }}
      />

      {withoutRiskResult && withRiskResult && (
        <div style={{ padding: 16, backgroundColor: '#f0f5ff', borderRadius: 8, marginBottom: 24 }}>
          <Text style={{ fontSize: 13, color: '#1890ff' }}>
            💡 <strong>解读：</strong>
            启用风控后，收益
            {withRiskResult.total_return > withoutRiskResult.total_return ? '提升' : '降低'}
            {Math.abs((withRiskResult.total_return - withoutRiskResult.total_return) * 100).toFixed(2)}%，
            同时最大回撤
            {Math.abs(withRiskResult.max_drawdown) < Math.abs(withoutRiskResult.max_drawdown) ? '降低' : '增加'}
            {Math.abs(Math.abs(withRiskResult.max_drawdown) - Math.abs(withoutRiskResult.max_drawdown) * 100).toFixed(2)}%，
            风险调整后的收益
            {(withRiskResult.sharpe_ratio || 0) > (withoutRiskResult.sharpe_ratio || 0) ? '显著提升' : '有所下降'}。
          </Text>
        </div>
      )}

      <Divider />

      {/* 风控触发明细 */}
      <Title level={4}>🎯 风控触发明细</Title>

      {riskEvents.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#bfbfbf' }}>
          本次回测未触发风控事件
        </div>
      ) : (
        <>
          {/* 止损事件 */}
          {groupedEvents.stop_loss.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <Text strong>
                {renderEventTag('stop_loss')} 止损事件（{groupedEvents.stop_loss.length}次）
              </Text>
              <Timeline style={{ marginTop: 12 }}>
                {groupedEvents.stop_loss.map((event, index) => (
                  <Timeline.Item key={index} color="orange">
                    <div>
                      <Text strong>{event.date}</Text> - {event.symbol || '全部持仓'}
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        触发价格：{event.price ? formatCurrency(event.price) : '-'} |
                        成本价格：{event.cost_price ? formatCurrency(event.cost_price) : '-'}
                      </Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {event.reason}
                      </Text>
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            </div>
          )}

          {/* 止盈事件 */}
          {groupedEvents.stop_profit.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <Text strong>
                {renderEventTag('stop_profit')} 止盈事件（{groupedEvents.stop_profit.length}次）
              </Text>
              <Timeline style={{ marginTop: 12 }}>
                {groupedEvents.stop_profit.map((event, index) => (
                  <Timeline.Item key={index} color="gold">
                    <div>
                      <Text strong>{event.date}</Text> - {event.symbol || '全部持仓'}
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        触发价格：{event.price ? formatCurrency(event.price) : '-'} |
                        成本价格：{event.cost_price ? formatCurrency(event.cost_price) : '-'}
                      </Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {event.reason}
                      </Text>
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            </div>
          )}

          {/* 回撤保护事件 */}
          {groupedEvents.drawdown_protection.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <Text strong>
                {renderEventTag('drawdown_protection')} 回撤保护（{groupedEvents.drawdown_protection.length}次）
              </Text>
              <Timeline style={{ marginTop: 12 }}>
                {groupedEvents.drawdown_protection.map((event, index) => (
                  <Timeline.Item key={index} color="red">
                    <div>
                      <Text strong>{event.date}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {event.reason}
                      </Text>
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            </div>
          )}

          {/* 拒绝订单事件 */}
          {groupedEvents.rejected_order.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <Text strong>
                {renderEventTag('rejected_order')} 拒绝订单（{groupedEvents.rejected_order.length}次）
              </Text>
              <Timeline style={{ marginTop: 12 }}>
                {groupedEvents.rejected_order.map((event, index) => (
                  <Timeline.Item key={index} color="gray">
                    <div>
                      <Text strong>{event.date}</Text> - {event.symbol || ''}
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {event.reason}
                      </Text>
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            </div>
          )}
        </>
      )}
    </Drawer>
  );
}
