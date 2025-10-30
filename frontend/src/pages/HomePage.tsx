import { useNavigate } from 'react-router-dom';
import { Card, Button, Typography, Space, Row, Col } from 'antd';
import { RocketOutlined, LineChartOutlined, ThunderboltOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

export default function HomePage() {
  const navigate = useNavigate();

  const features = [
    {
      icon: <LineChartOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
      title: '技术指标回测',
      description: '支持均线、MACD、KDJ、RSI等多种技术指标策略回测',
    },
    {
      icon: <ThunderboltOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
      title: '预设策略',
      description: '内置早晨之星、MACD金叉等经典交易策略，一键回测',
    },
    {
      icon: <RocketOutlined style={{ fontSize: 48, color: '#faad14' }} />,
      title: '数据可视化',
      description: 'K线图、收益曲线、交易明细，全方位展示回测结果',
    },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '40px 0' }}>
      <Card bordered={false}>
        <div style={{ textAlign: 'center', marginBottom: 60 }}>
          <Title level={1} style={{ marginBottom: 16 }}>
            欢迎使用股票回测系统
          </Title>
          <Paragraph style={{ fontSize: 18, color: '#595959', marginBottom: 32 }}>
            帮助散户投资者验证交易理论，提升交易胜率
          </Paragraph>
          <Button
            type="primary"
            size="large"
            onClick={() => navigate('/backtest')}
            style={{ height: 48, fontSize: 16, padding: '0 48px' }}
          >
            开始回测
          </Button>
        </div>

        <Row gutter={[24, 24]} style={{ marginTop: 60 }}>
          {features.map((feature, index) => (
            <Col xs={24} md={8} key={index}>
              <Card hoverable>
                <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
                  {feature.icon}
                  <Title level={4}>{feature.title}</Title>
                  <Paragraph>{feature.description}</Paragraph>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>

        <Card style={{ marginTop: 40, background: '#f6f8fa' }} bordered={false}>
          <Title level={4}>如何使用？</Title>
          <Space direction="vertical" size="middle">
            <Paragraph>
              <strong>1. 选择股票</strong> - 输入股票代码或名称进行搜索
            </Paragraph>
            <Paragraph>
              <strong>2. 选择策略</strong> - 从预设策略中选择交易理论
            </Paragraph>
            <Paragraph>
              <strong>3. 设置参数</strong> - 配置回测时间区间和初始资金
            </Paragraph>
            <Paragraph>
              <strong>4. 查看结果</strong> - 分析收益率、胜率、最大回撤等指标
            </Paragraph>
          </Space>
        </Card>
      </Card>
    </div>
  );
}
