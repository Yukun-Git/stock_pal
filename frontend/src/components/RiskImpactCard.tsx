import { Card, Row, Col, Statistic, Button } from 'antd';
import { ArrowDownOutlined, ArrowUpOutlined } from '@ant-design/icons';
import type { RiskStats } from '@/types';
import { formatPercent, formatCurrency } from '@/utils/format';

interface RiskImpactCardProps {
  riskStats: RiskStats;
  onViewComparison?: () => void;
}

export default function RiskImpactCard({ riskStats, onViewComparison }: RiskImpactCardProps) {
  const {
    stop_loss_count,
    stop_profit_count,
    drawdown_protection_count,
    rejected_orders_count,
    stop_loss_saved_loss,
    stop_profit_locked_profit,
    drawdown_protection_saved_loss,
  } = riskStats;

  return (
    <Card
      title={
        <span>
          <span style={{ marginRight: 8 }}>📊</span>
          风控影响分析
        </span>
      }
      extra={
        onViewComparison && (
          <Button type="link" onClick={onViewComparison}>
            查看详细对比
          </Button>
        )
      }
      style={{ marginTop: 24 }}
    >
      <Row gutter={[16, 16]}>
        {/* 止损触发 */}
        <Col xs={24} sm={12} md={8}>
          <div
            style={{
              padding: 20,
              backgroundColor: '#fff7e6',
              borderRadius: 8,
              border: '1px solid #ffd591',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
              止损触发
            </div>
            <div style={{ fontSize: 32, fontWeight: 700, color: '#fa8c16', marginBottom: 8 }}>
              {stop_loss_count} 次
            </div>
            <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 4 }}>
              <ArrowDownOutlined style={{ color: '#fa8c16', marginRight: 4 }} />
              避免亏损
            </div>
            {stop_loss_saved_loss !== undefined && (
              <div style={{ fontSize: 16, fontWeight: 600, color: '#fa8c16' }}>
                {formatPercent(stop_loss_saved_loss)}
              </div>
            )}
          </div>
        </Col>

        {/* 止盈触发 */}
        <Col xs={24} sm={12} md={8}>
          <div
            style={{
              padding: 20,
              backgroundColor: '#f6ffed',
              borderRadius: 8,
              border: '1px solid #b7eb8f',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
              止盈触发
            </div>
            <div style={{ fontSize: 32, fontWeight: 700, color: '#52c41a', marginBottom: 8 }}>
              {stop_profit_count} 次
            </div>
            <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 4 }}>
              <ArrowUpOutlined style={{ color: '#52c41a', marginRight: 4 }} />
              锁定收益
            </div>
            {stop_profit_locked_profit !== undefined && (
              <div style={{ fontSize: 16, fontWeight: 600, color: '#52c41a' }}>
                {formatPercent(stop_profit_locked_profit)}
              </div>
            )}
          </div>
        </Col>

        {/* 回撤保护 */}
        <Col xs={24} sm={12} md={8}>
          <div
            style={{
              padding: 20,
              backgroundColor: '#fff1f0',
              borderRadius: 8,
              border: '1px solid #ffccc7',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
              回撤保护
            </div>
            <div style={{ fontSize: 32, fontWeight: 700, color: '#f5222d', marginBottom: 8 }}>
              {drawdown_protection_count} 次
            </div>
            <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 4 }}>
              <ArrowDownOutlined style={{ color: '#f5222d', marginRight: 4 }} />
              止住出血
            </div>
            {drawdown_protection_saved_loss !== undefined && (
              <div style={{ fontSize: 16, fontWeight: 600, color: '#f5222d' }}>
                {formatPercent(drawdown_protection_saved_loss)}
              </div>
            )}
          </div>
        </Col>

        {/* 拒绝订单 */}
        <Col xs={24} sm={12} md={8}>
          <div
            style={{
              padding: 20,
              backgroundColor: '#f5f5f5',
              borderRadius: 8,
              border: '1px solid #d9d9d9',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
              拒绝订单
            </div>
            <div style={{ fontSize: 32, fontWeight: 700, color: '#8c8c8c', marginBottom: 8 }}>
              {rejected_orders_count} 次
            </div>
            <div style={{ fontSize: 12, color: '#8c8c8c' }}>
              🛡️ 防止超仓
            </div>
          </div>
        </Col>

        {/* 总体效果 */}
        <Col xs={24} sm={12} md={16}>
          <div
            style={{
              padding: 20,
              backgroundColor: '#e6f7ff',
              borderRadius: 8,
              border: '1px solid #91d5ff',
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
              总体效果
            </div>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="风控触发总计"
                  value={stop_loss_count + stop_profit_count + drawdown_protection_count}
                  suffix="次"
                  valueStyle={{ color: '#1890ff', fontSize: 24 }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="订单拦截"
                  value={rejected_orders_count}
                  suffix="次"
                  valueStyle={{ color: '#8c8c8c', fontSize: 24 }}
                />
              </Col>
            </Row>
          </div>
        </Col>
      </Row>

      {/* 提示信息 */}
      {(stop_loss_count > 0 || stop_profit_count > 0 || drawdown_protection_count > 0) && (
        <div
          style={{
            marginTop: 16,
            padding: 12,
            backgroundColor: '#f0f5ff',
            borderRadius: 6,
            fontSize: 13,
            color: '#1890ff',
          }}
        >
          💡 风控系统已为您执行 {stop_loss_count + stop_profit_count + drawdown_protection_count} 次风险控制操作，
          {stop_loss_count > 0 && `帮助避免了额外亏损，`}
          {stop_profit_count > 0 && `锁定了部分收益，`}
          {drawdown_protection_count > 0 && `在回撤时及时保护了资金。`}
        </div>
      )}
    </Card>
  );
}
