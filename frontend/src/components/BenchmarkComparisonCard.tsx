import { Card, Row, Col, Statistic, Typography, Tooltip, Empty } from 'antd';
import { InfoCircleOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import type { BacktestResult, Benchmark } from '@/types';
import { formatPercent } from '@/utils/format';

const { Title, Text } = Typography;

interface BenchmarkComparisonCardProps {
  results: BacktestResult;
  benchmark?: Benchmark;
}

export default function BenchmarkComparisonCard({ results, benchmark }: BenchmarkComparisonCardProps) {
  // 如果没有基准数据，不显示组件
  if (!benchmark) {
    return null;
  }

  // 检查是否有基准对比指标
  const hasComparisonMetrics =
    results.alpha !== undefined &&
    results.beta !== undefined &&
    results.information_ratio !== undefined &&
    results.tracking_error !== undefined;

  if (!hasComparisonMetrics) {
    return (
      <Card>
        <Title level={5}>📊 基准对比</Title>
        <Empty description="基准对比指标不可用" />
      </Card>
    );
  }

  // 判断Alpha的颜色（正值为绿色，负值为红色）
  const alphaColor = (results.alpha || 0) >= 0 ? '#3f8600' : '#cf1322';
  const alphaIcon = (results.alpha || 0) >= 0 ? <RiseOutlined /> : <FallOutlined />;

  // 判断信息比率的颜色
  const irColor = (results.information_ratio || 0) >= 0 ? '#3f8600' : '#cf1322';

  return (
    <Card>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
        <Title level={5} style={{ margin: 0, flex: 1 }}>
          📊 基准对比
        </Title>
        <Text type="secondary" style={{ fontSize: 12 }}>
          vs {benchmark.name}
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        {/* Alpha */}
        <Col xs={24} sm={12} md={6}>
          <Tooltip
            title={
              <div>
                <div><strong>Alpha（超额收益）</strong></div>
                <div style={{ marginTop: 4 }}>衡量策略相对基准的超额收益能力。</div>
                <div style={{ marginTop: 4 }}>
                  <strong>正值：</strong>策略跑赢基准<br />
                  <strong>负值：</strong>策略跑输基准
                </div>
              </div>
            }
          >
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title={
                  <span>
                    Alpha <InfoCircleOutlined style={{ fontSize: 12, color: '#8c8c8c' }} />
                  </span>
                }
                value={formatPercent(results.alpha || 0)}
                valueStyle={{ color: alphaColor, fontSize: 20 }}
                prefix={alphaIcon}
              />
            </Card>
          </Tooltip>
        </Col>

        {/* Beta */}
        <Col xs={24} sm={12} md={6}>
          <Tooltip
            title={
              <div>
                <div><strong>Beta（系统风险）</strong></div>
                <div style={{ marginTop: 4 }}>衡量策略对基准的敏感度。</div>
                <div style={{ marginTop: 4 }}>
                  <strong>Beta = 1：</strong>与基准同步<br />
                  <strong>Beta &gt; 1：</strong>波动性更大<br />
                  <strong>Beta &lt; 1：</strong>波动性更小
                </div>
              </div>
            }
          >
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title={
                  <span>
                    Beta <InfoCircleOutlined style={{ fontSize: 12, color: '#8c8c8c' }} />
                  </span>
                }
                value={(results.beta || 0).toFixed(2)}
                valueStyle={{ fontSize: 20 }}
              />
            </Card>
          </Tooltip>
        </Col>

        {/* Information Ratio */}
        <Col xs={24} sm={12} md={6}>
          <Tooltip
            title={
              <div>
                <div><strong>信息比率（IR）</strong></div>
                <div style={{ marginTop: 4 }}>衡量超额收益的稳定性。</div>
                <div style={{ marginTop: 4 }}>
                  <strong>IR &gt; 0.5：</strong>优秀<br />
                  <strong>IR &lt; 0：</strong>表现不佳
                </div>
              </div>
            }
          >
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title={
                  <span>
                    信息比率 <InfoCircleOutlined style={{ fontSize: 12, color: '#8c8c8c' }} />
                  </span>
                }
                value={(results.information_ratio || 0).toFixed(2)}
                valueStyle={{ color: irColor, fontSize: 20 }}
              />
            </Card>
          </Tooltip>
        </Col>

        {/* Tracking Error */}
        <Col xs={24} sm={12} md={6}>
          <Tooltip
            title={
              <div>
                <div><strong>跟踪误差（TE）</strong></div>
                <div style={{ marginTop: 4 }}>策略收益率偏离基准的程度（年化标准差）。</div>
                <div style={{ marginTop: 4 }}>
                  <strong>数值越小：</strong>与基准越接近<br />
                  <strong>数值越大：</strong>偏离基准越多
                </div>
              </div>
            }
          >
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title={
                  <span>
                    跟踪误差 <InfoCircleOutlined style={{ fontSize: 12, color: '#8c8c8c' }} />
                  </span>
                }
                value={formatPercent(results.tracking_error || 0)}
                valueStyle={{ fontSize: 20 }}
              />
            </Card>
          </Tooltip>
        </Col>
      </Row>

      {/* 基准指标摘要 */}
      <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          <strong>基准表现：</strong>
          收益率 {formatPercent(benchmark.metrics.total_return)} |
          年化 {formatPercent(benchmark.metrics.cagr)} |
          夏普 {benchmark.metrics.sharpe_ratio.toFixed(2)} |
          最大回撤 {formatPercent(benchmark.metrics.max_drawdown)}
        </Text>
      </div>
    </Card>
  );
}
