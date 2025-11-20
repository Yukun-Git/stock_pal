import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tag,
  Button,
  Space,
  Statistic,
  Row,
  Col,
  Tooltip,
  Typography,
  message,
  Spin,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  QuestionCircleOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { adapterApi } from '@/services/api';
import type {
  AdapterStatus,
  AdapterHealthStatus,
  HealthCheckResponse,
} from '@/types';

const { Title, Text } = Typography;

const DataSourcePage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [healthChecking, setHealthChecking] = useState(false);
  const [adapters, setAdapters] = useState<AdapterStatus[]>([]);
  const [healthSummary, setHealthSummary] = useState<HealthCheckResponse | null>(null);

  // 加载适配器状态
  const loadAdapterStatus = async () => {
    setLoading(true);
    try {
      const data = await adapterApi.getAdapterStatus();
      setAdapters(data);
    } catch (error) {
      message.error('加载数据源状态失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 执行健康检查
  const runHealthCheck = async () => {
    setHealthChecking(true);
    try {
      const result = await adapterApi.healthCheck();
      setHealthSummary(result);
      message.success('健康检查完成');
      // 重新加载状态
      await loadAdapterStatus();
    } catch (error) {
      message.error('健康检查失败');
      console.error(error);
    } finally {
      setHealthChecking(false);
    }
  };

  useEffect(() => {
    loadAdapterStatus();
  }, []);

  // 健康状态图标
  const getHealthIcon = (status: AdapterHealthStatus) => {
    switch (status) {
      case 'online':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />;
      case 'offline':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#faad14', fontSize: 20 }} />;
      default:
        return <QuestionCircleOutlined style={{ color: '#d9d9d9', fontSize: 20 }} />;
    }
  };

  // 健康状态标签
  const getHealthTag = (status: AdapterHealthStatus) => {
    const config = {
      online: { color: 'success', text: '在线' },
      offline: { color: 'error', text: '离线' },
      error: { color: 'warning', text: '错误' },
      unknown: { color: 'default', text: '未知' },
    };
    const { color, text } = config[status] || config.unknown;
    return <Tag color={color}>{text}</Tag>;
  };

  // 表格列定义
  const columns: ColumnsType<AdapterStatus> = [
    {
      title: '数据源',
      dataIndex: 'display_name',
      key: 'display_name',
      width: 200,
      render: (text, record) => (
        <Space>
          {getHealthIcon(record.health_status)}
          <div>
            <div><strong>{text}</strong></div>
            <Text type="secondary" style={{ fontSize: 12 }}>{record.name}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '支持市场',
      dataIndex: 'supported_markets',
      key: 'supported_markets',
      width: 180,
      render: (markets: string[]) => (
        <Space wrap>
          {markets.map((market) => (
            <Tag key={market}>{market}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '健康状态',
      dataIndex: 'health_status',
      key: 'health_status',
      width: 100,
      align: 'center',
      render: (status: AdapterHealthStatus) => getHealthTag(status),
    },
    {
      title: '成功次数',
      key: 'success_count',
      width: 100,
      align: 'right',
      render: (_, record) => (
        <Text strong style={{ color: '#52c41a' }}>
          {record.metrics?.success_count || 0}
        </Text>
      ),
    },
    {
      title: '失败次数',
      key: 'fail_count',
      width: 100,
      align: 'right',
      render: (_, record) => (
        <Text strong style={{ color: '#ff4d4f' }}>
          {record.metrics?.fail_count || 0}
        </Text>
      ),
    },
    {
      title: '平均响应',
      key: 'avg_response',
      width: 120,
      align: 'right',
      render: (_, record) => {
        const avgMs = record.metrics?.avg_response_ms;
        if (!avgMs) return <Text type="secondary">-</Text>;
        const color = avgMs < 500 ? '#52c41a' : avgMs < 2000 ? '#faad14' : '#ff4d4f';
        return <Text strong style={{ color }}>{avgMs.toFixed(0)}ms</Text>;
      },
    },
    {
      title: '最后成功',
      dataIndex: ['metrics', 'last_success'],
      key: 'last_success',
      width: 160,
      render: (time: string | null) => {
        if (!time) return <Text type="secondary">-</Text>;
        const date = new Date(time);
        return (
          <Tooltip title={date.toLocaleString()}>
            <Text>{date.toLocaleTimeString()}</Text>
          </Tooltip>
        );
      },
    },
    {
      title: '超时设置',
      dataIndex: 'timeout',
      key: 'timeout',
      width: 100,
      align: 'right',
      render: (timeout: number) => <Text>{timeout}s</Text>,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 标题和操作 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>数据源管理</Title>
          <Text type="secondary">监控和管理股票数据源适配器</Text>
        </Col>
        <Col>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadAdapterStatus}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={runHealthCheck}
              loading={healthChecking}
            >
              健康检查
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 健康统计卡片 */}
      {healthSummary && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总数据源"
                value={healthSummary.summary.total}
                prefix={<ThunderboltOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="在线"
                value={healthSummary.summary.online}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="离线"
                value={healthSummary.summary.offline}
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<CloseCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="错误"
                value={healthSummary.summary.error}
                valueStyle={{ color: '#faad14' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 数据源列表 */}
      <Card title="数据源列表" bordered={false}>
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={adapters}
            rowKey="name"
            pagination={false}
            size="middle"
          />
        </Spin>
      </Card>

      {/* 使用说明 */}
      <Card
        title="使用说明"
        style={{ marginTop: 16 }}
        size="small"
      >
        <Space direction="vertical">
          <Text>
            • <strong>健康状态</strong>: 通过实时测试判断数据源是否可用
          </Text>
          <Text>
            • <strong>故障转移</strong>: 当首选数据源失败时,系统会自动切换到备用数据源
          </Text>
          <Text>
            • <strong>性能指标</strong>: 显示每个数据源的成功/失败次数和平均响应时间
          </Text>
          <Text type="secondary">
            建议定期执行健康检查以确保系统稳定性
          </Text>
        </Space>
      </Card>
    </div>
  );
};

export default DataSourcePage;
