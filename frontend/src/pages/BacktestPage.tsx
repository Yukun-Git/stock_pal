import { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Select,
  DatePicker,
  InputNumber,
  Button,
  Row,
  Col,
  Statistic,
  Table,
  message,
  Spin,
  Typography,
} from 'antd';
import { SearchOutlined, ThunderboltOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Strategy, BacktestResponse } from '@/types';
import { strategyApi, backtestApi } from '@/services/api';
import { formatCurrency, formatPercent, toApiDateFormat } from '@/utils/format';
import KLineChart from '@/components/KLineChart';
import EquityCurveChart from '@/components/EquityCurveChart';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

// Fixed stock list (A-share + HK stocks)
const STOCK_LIST = [
  // Hong Kong stocks
  { name: "腾讯控股", code: "00700.HK" },
  { name: "阿里巴巴-SW", code: "09988.HK" },
  { name: "美团-W", code: "03690.HK" },
  { name: "小米集团-W", code: "01810.HK" },
  { name: "京东集团-SW", code: "09618.HK" },
  { name: "快手-W", code: "01024.HK" },
  { name: "网易-S", code: "09999.HK" },
  { name: "百度集团-SW", code: "09888.HK" },
  { name: "哔哩哔哩-W", code: "09626.HK" },
  { name: "携程集团-S", code: "09961.HK" },
  // A-share stocks
  { name: "贵州茅台", code: "600519.SH" },
  { name: "宁德时代", code: "300750.SZ" },
  { name: "五粮液", code: "000858.SZ" },
  { name: "比亚迪", code: "002594.SZ" },
  { name: "招商银行", code: "600036.SH" },
  { name: "中国平安", code: "601318.SH" },
  { name: "工商银行", code: "601398.SH" },
  { name: "美的集团", code: "000333.SZ" },
  { name: "隆基绿能", code: "601012.SH" },
  { name: "紫金矿业", code: "601899.SH" },
];

export default function BacktestPage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [result, setResult] = useState<BacktestResponse | null>(null);

  // Load strategies on mount
  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      const data = await strategyApi.getStrategies();
      setStrategies(data);
    } catch (error) {
      message.error('加载策略列表失败');
    }
  };

  const handleStrategyChange = (strategyId: string) => {
    const strategy = strategies.find(s => s.id === strategyId);
    setSelectedStrategy(strategy || null);

    // Reset strategy parameter form values to defaults
    if (strategy && strategy.parameters.length > 0) {
      const defaultParams: Record<string, any> = {};
      strategy.parameters.forEach(param => {
        defaultParams[`param_${param.name}`] = param.default;
      });
      form.setFieldsValue(defaultParams);
    }
  };

  const handleSubmit = async (values: any) => {
    setLoading(true);
    setResult(null);

    try {
      const startDate = values.dateRange ? toApiDateFormat(values.dateRange[0].toDate()) : undefined;
      const endDate = values.dateRange ? toApiDateFormat(values.dateRange[1].toDate()) : undefined;

      // Extract strategy parameters from form values
      const strategy_params: Record<string, any> = {};
      if (selectedStrategy && selectedStrategy.parameters.length > 0) {
        selectedStrategy.parameters.forEach(param => {
          const formKey = `param_${param.name}`;
          if (values[formKey] !== undefined) {
            strategy_params[param.name] = values[formKey];
          }
        });
      }

      const response = await backtestApi.runBacktest({
        symbol: values.symbol,
        strategy_id: values.strategy,
        start_date: startDate,
        end_date: endDate,
        initial_capital: values.initialCapital,
        commission_rate: values.commissionRate,
        strategy_params,
      });

      setResult(response);
      message.success('回测完成！');
    } catch (error: any) {
      message.error(error?.response?.data?.error || '回测失败，请检查参数');
    } finally {
      setLoading(false);
    }
  };

  const tradeColumns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Text strong style={{ color: type === 'buy' ? '#ff4d4f' : '#52c41a' }}>
          {type === 'buy' ? '买入' : '卖出'}
        </Text>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '数量',
      dataIndex: 'shares',
      key: 'shares',
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => formatCurrency(amount),
    },
    {
      title: '手续费',
      dataIndex: 'commission',
      key: 'commission',
      render: (commission: number) => formatCurrency(commission),
    },
    {
      title: '盈亏',
      dataIndex: 'profit',
      key: 'profit',
      render: (profit: number) => {
        if (profit === undefined) return '-';
        return (
          <Text style={{ color: profit >= 0 ? '#ff4d4f' : '#52c41a' }}>
            {formatCurrency(profit)}
          </Text>
        );
      },
    },
    {
      title: '盈亏比例',
      dataIndex: 'profit_pct',
      key: 'profit_pct',
      render: (pct: number) => {
        if (pct === undefined) return '-';
        return (
          <Text style={{ color: pct >= 0 ? '#ff4d4f' : '#52c41a' }}>
            {formatPercent(pct)}
          </Text>
        );
      },
    },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Card>
        <Title level={3}>
          <ThunderboltOutlined /> 策略回测
        </Title>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            dateRange: [dayjs().subtract(2, 'year'), dayjs()],
            initialCapital: 100000,
            commissionRate: 0.0003,
          }}
        >
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="股票代码/名称"
                name="symbol"
                rules={[{ required: true, message: '请选择股票' }]}
              >
                <Select
                  placeholder="选择股票"
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  options={STOCK_LIST.map(stock => ({
                    value: stock.code,
                    label: `${stock.code} - ${stock.name}`,
                  }))}
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="交易策略"
                name="strategy"
                rules={[{ required: true, message: '请选择交易策略' }]}
              >
                <Select placeholder="选择交易策略" onChange={handleStrategyChange}>
                  {strategies.map(strategy => (
                    <Select.Option key={strategy.id} value={strategy.id}>
                      {strategy.name} - {strategy.description}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item label="回测时间区间" name="dateRange">
                <RangePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          {/* Strategy Parameters - Dynamic Form */}
          {selectedStrategy && selectedStrategy.parameters.length > 0 && (
            <Row gutter={16} style={{ marginTop: 8 }}>
              <Col span={24}>
                <Card size="small" title={`${selectedStrategy.name} 策略参数`} style={{ marginBottom: 16 }}>
                  <Row gutter={16}>
                    {selectedStrategy.parameters.map((param) => (
                      <Col xs={24} md={8} key={param.name}>
                        <Form.Item
                          label={param.label}
                          name={`param_${param.name}`}
                          tooltip={param.description}
                          initialValue={param.default}
                        >
                          <InputNumber
                            style={{ width: '100%' }}
                            min={param.min}
                            max={param.max}
                            step={param.type === 'integer' ? 1 : 0.1}
                            precision={param.type === 'integer' ? 0 : 2}
                          />
                        </Form.Item>
                      </Col>
                    ))}
                  </Row>
                </Card>
              </Col>
            </Row>
          )}

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item label="初始资金" name="initialCapital">
                <InputNumber
                  style={{ width: '100%' }}
                  min={1000}
                  step={10000}
                  formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={(value) => value?.replace(/¥\s?|(,*)/g, '') as any}
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item label="手续费率" name="commissionRate">
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={0.01}
                  step={0.0001}
                  formatter={(value) => value ? `${(Number(value) * 100).toFixed(2)}%` : ''}
                  parser={(value) => (value ? Number(value.replace('%', '')) / 100 : 0) as any}
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item label=" ">
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<SearchOutlined />}
                  size="large"
                  block
                >
                  开始回测
                </Button>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      {loading && (
        <Card style={{ marginTop: 24, textAlign: 'center', padding: 60 }}>
          <Spin size="large" tip="回测计算中，请稍候..." />
        </Card>
      )}

      {result && !loading && (
        <>
          {/* Results Statistics */}
          <Card title="回测结果" style={{ marginTop: 24 }}>
            <Row gutter={16}>
              <Col xs={12} sm={8} md={6}>
                <Statistic
                  title="总收益率"
                  value={result.results.total_return}
                  precision={2}
                  suffix="%"
                  valueStyle={{
                    color: result.results.total_return >= 0 ? '#ff4d4f' : '#52c41a',
                  }}
                />
              </Col>
              <Col xs={12} sm={8} md={6}>
                <Statistic
                  title="最终资金"
                  value={result.results.final_capital}
                  precision={2}
                  prefix="¥"
                />
              </Col>
              <Col xs={12} sm={8} md={6}>
                <Statistic
                  title="交易次数"
                  value={result.results.total_trades}
                  suffix="次"
                />
              </Col>
              <Col xs={12} sm={8} md={6}>
                <Statistic
                  title="胜率"
                  value={result.results.win_rate}
                  precision={2}
                  suffix="%"
                />
              </Col>
              <Col xs={12} sm={8} md={6}>
                <Statistic
                  title="最大回撤"
                  value={Math.abs(result.results.max_drawdown)}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col xs={12} sm={8} md={6}>
                <Statistic
                  title="盈利因子"
                  value={result.results.profit_factor}
                  precision={2}
                />
              </Col>
              <Col xs={12} sm={8} md={6}>
                <Statistic
                  title="平均盈利"
                  value={result.results.avg_profit}
                  precision={2}
                  prefix="¥"
                />
              </Col>
              <Col xs={12} sm={8} md={6}>
                <Statistic
                  title="平均亏损"
                  value={Math.abs(result.results.avg_loss)}
                  precision={2}
                  prefix="¥"
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
            </Row>
          </Card>

          {/* K-Line Chart */}
          <Card title="K线图与买卖点" style={{ marginTop: 24 }}>
            <KLineChart
              data={result.klines}
              buyPoints={result.buy_points}
              sellPoints={result.sell_points}
              height={500}
            />
          </Card>

          {/* Equity Curve */}
          <Card title="资产曲线" style={{ marginTop: 24 }}>
            <EquityCurveChart
              data={result.equity_curve}
              initialCapital={result.results.initial_capital}
              height={300}
            />
          </Card>

          {/* Trade History */}
          <Card title="交易明细" style={{ marginTop: 24 }}>
            <Table
              dataSource={result.trades}
              columns={tradeColumns}
              rowKey={(record, index) => `${record.date}-${index}`}
              pagination={{ pageSize: 10 }}
              scroll={{ x: 800 }}
            />
          </Card>
        </>
      )}
    </div>
  );
}
