import { Card, Row, Col, Statistic, Tooltip } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';
import type { CSSProperties, ReactNode } from 'react';

/**
 * 单个指标配置
 */
export interface MetricItem {
  /** 指标标题 */
  title: string;
  /** 指标值 */
  value: number | string;
  /** 小数精度 */
  precision?: number;
  /** 前缀（如 ¥） */
  prefix?: string;
  /** 后缀（如 %） */
  suffix?: string;
  /** 值的样式 */
  valueStyle?: CSSProperties;
  /** Tooltip提示文字 */
  tooltip?: string;
}

/**
 * MetricsCard 组件属性
 */
interface MetricsCardProps {
  /** 卡片标题 */
  title: string;
  /** 标题图标 */
  icon?: ReactNode;
  /** 指标列表 */
  metrics: MetricItem[];
  /** 每行显示列数（默认4） */
  columns?: number;
  /** 额外的样式 */
  style?: CSSProperties;
}

/**
 * 指标展示卡片组件
 *
 * 用于分组展示回测性能指标
 *
 * @example
 * ```tsx
 * <MetricsCard
 *   title="收益指标"
 *   icon="📊"
 *   metrics={[
 *     { title: '总收益率', value: 12.5, suffix: '%', tooltip: '整个回测期间的总收益' }
 *   ]}
 *   columns={4}
 * />
 * ```
 */
export default function MetricsCard({
  title,
  icon,
  metrics,
  columns = 4,
  style
}: MetricsCardProps) {
  // 根据列数计算span值
  const span = 24 / columns;

  return (
    <Card
      title={
        <span>
          {icon && <span style={{ marginRight: 8 }}>{icon}</span>}
          {title}
        </span>
      }
      style={{ marginTop: 24, ...style }}
      bordered={true}
      hoverable={false}
    >
      <Row gutter={[16, 16]}>
        {metrics.map((metric, index) => (
          <Col
            xs={24}
            sm={12}
            md={span}
            key={index}
          >
            <Statistic
              title={
                <span>
                  {metric.title}
                  {metric.tooltip && (
                    <Tooltip title={metric.tooltip} placement="top">
                      <QuestionCircleOutlined
                        style={{
                          marginLeft: 4,
                          color: '#8c8c8c',
                          fontSize: 12,
                          cursor: 'help'
                        }}
                      />
                    </Tooltip>
                  )}
                </span>
              }
              value={metric.value}
              precision={metric.precision}
              prefix={metric.prefix}
              suffix={metric.suffix}
              valueStyle={{
                fontSize: 24,
                fontWeight: 600,
                ...metric.valueStyle
              }}
            />
          </Col>
        ))}
      </Row>
    </Card>
  );
}
