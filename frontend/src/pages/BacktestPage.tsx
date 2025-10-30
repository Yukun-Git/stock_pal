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
  AutoComplete,
} from 'antd';
import { SearchOutlined, ThunderboltOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Stock, Strategy, BacktestResponse } from '@/types';
import { stockApi, strategyApi, backtestApi } from '@/services/api';
import { formatCurrency, formatPercent, toApiDateFormat } from '@/utils/format';
import KLineChart from '@/components/KLineChart';
import EquityCurveChart from '@/components/EquityCurveChart';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

export default function BacktestPage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [stockOptions, setStockOptions] = useState<Stock[]>([]);
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

  const handleStockSearch = async (keyword: string) => {
    if (!keyword || keyword.length < 2) {
      setStockOptions([]);
      return;
    }

    setSearchLoading(true);
    try {
      const stocks = await stockApi.searchStocks(keyword);
      setStockOptions(stocks);
    } catch (error) {
      message.error('搜索股票失败');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSubmit = async (values: any) => {
    setLoading(true);
    setResult(null);

    try {
      const startDate = values.dateRange ? toApiDateFormat(values.dateRange[0].toDate()) : undefined;
      const endDate = values.dateRange ? toApiDateFormat(values.dateRange[1].toDate()) : undefined;

      const response = await backtestApi.runBacktest({
        symbol: values.symbol,
        strategy_id: values.strategy,
        start_date: startDate,
        end_date: endDate,
        initial_capital: values.initialCapital,
        commission_rate: values.commissionRate,
        strategy_params: {},
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
                rules={[{ required: true, message: '请输入股票代码或名称' }]}
              >
                <AutoComplete
                  options={stockOptions.map(stock => ({
                    value: stock.code,
                    label: `${stock.code} - ${stock.name}`,
                  }))}
                  onSearch={handleStockSearch}
                  placeholder="输入股票代码或名称搜索"
                  notFoundContent={searchLoading ? <Spin size="small" /> : null}
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="交易策略"
                name="strategy"
                rules={[{ required: true, message: '请选择交易策略' }]}
              >
                <Select placeholder="选择交易策略">
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
