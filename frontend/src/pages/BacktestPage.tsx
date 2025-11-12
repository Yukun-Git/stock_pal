import { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Select,
  InputNumber,
  Button,
  Row,
  Col,
  Statistic,
  Table,
  message,
  Spin,
  Typography,
  Input,
} from 'antd';
import { SearchOutlined, ThunderboltOutlined, CheckCircleOutlined, FileTextOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Strategy, BacktestResponse } from '@/types';
import { strategyApi, backtestApi } from '@/services/api';
import { formatCurrency, formatPercent, toApiDateFormat } from '@/utils/format';
import KLineChart from '@/components/KLineChart';
import EquityCurveChart from '@/components/EquityCurveChart';
import StrategyDocModal from '@/components/StrategyDocModal';
import { ParameterInput } from '@/components/parameters';
import { SignalAnalysisCard } from '@/components/signalAnalysis';

const { Title, Text } = Typography;

// Time range options
const TIME_RANGES = [
  { label: '最近一个月', value: '1m', months: 1 },
  { label: '最近三个月', value: '3m', months: 3 },
  { label: '最近六个月', value: '6m', months: 6 },
  { label: '最近一年', value: '1y', months: 12 },
];

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
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [strategySearch, setStrategySearch] = useState('');
  const [docModalOpen, setDocModalOpen] = useState(false);
  const [currentDocStrategyId, setCurrentDocStrategyId] = useState<string | null>(null);

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

  const handleViewDocumentation = (strategyId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // 阻止冒泡，避免触发策略选择
    setCurrentDocStrategyId(strategyId);
    setDocModalOpen(true);
  };

  const handleStrategyToggle = (strategyId: string) => {
    let newSelected: string[];
    const isCurrentlySelected = selectedStrategies.includes(strategyId);

    if (isCurrentlySelected) {
      // Deselect - remove strategy
      newSelected = selectedStrategies.filter(id => id !== strategyId);
    } else {
      // Select - add strategy and set default parameters
      newSelected = [...selectedStrategies, strategyId];

      // Set default parameters for the newly selected strategy
      const strategy = strategies.find(s => s.id === strategyId);
      if (strategy && strategy.parameters.length > 0) {
        const defaultParams: Record<string, any> = {};
        strategy.parameters.forEach(param => {
          defaultParams[`param_${strategyId}_${param.name}`] = param.default;
        });
        form.setFieldsValue(defaultParams);
      }
    }

    setSelectedStrategies(newSelected);
  };

  const handleSubmit = async (values: any) => {
    // Validate strategy selection
    if (selectedStrategies.length === 0) {
      message.warning('请至少选择一个策略');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      // Calculate date range based on selected time range
      let startDate: string | undefined;
      let endDate: string | undefined;

      if (values.timeRange) {
        const timeRangeOption = TIME_RANGES.find(tr => tr.value === values.timeRange);
        if (timeRangeOption) {
          const end = dayjs();
          const start = end.subtract(timeRangeOption.months, 'month');
          startDate = toApiDateFormat(start.toDate());
          endDate = toApiDateFormat(end.toDate());
        }
      }

      // Extract strategy parameters from form values
      // Build per-strategy params: {"ma_cross": {...}, "macd_cross": {...}}
      const per_strategy_params: Record<string, Record<string, any>> = {};
      selectedStrategies.forEach(strategyId => {
        const strategy = strategies.find(s => s.id === strategyId);
        if (strategy && strategy.parameters.length > 0) {
          const strategyParams: Record<string, any> = {};
          strategy.parameters.forEach(param => {
            const formKey = `param_${strategyId}_${param.name}`;
            if (values[formKey] !== undefined) {
              strategyParams[param.name] = values[formKey];
            }
          });
          per_strategy_params[strategyId] = strategyParams;
        }
      });

      // Prepare request payload
      const requestData: any = {
        symbol: values.symbol,
        start_date: startDate,
        end_date: endDate,
        initial_capital: values.initialCapital,
        commission_rate: values.commissionRate,
        per_strategy_params,
      };

      // Use strategy_ids for multiple strategies, strategy_id for single
      if (selectedStrategies.length > 1) {
        requestData.strategy_ids = selectedStrategies;
        requestData.combine_mode = values.combineMode || 'AND';
        if (values.combineMode === 'VOTE') {
          requestData.vote_threshold = values.voteThreshold || 2;
        }
      } else if (selectedStrategies.length === 1) {
        requestData.strategy_id = selectedStrategies[0];
      }

      const response = await backtestApi.runBacktest(requestData);

      console.log('===== BACKTEST RESPONSE =====');
      console.log('Full response:', response);
      console.log('Has results:', !!response.results);
      console.log('Has klines:', !!response.klines);
      console.log('Has trades:', !!response.trades);
      console.log('Strategy type:', typeof response.strategy);
      console.log('Strategy value:', response.strategy);
      console.log('=============================');

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
    <div style={{ maxWidth: 1600, margin: '0 auto' }}>
      <Title level={2} style={{ marginBottom: 24 }}>
        <ThunderboltOutlined /> 策略回测
      </Title>

      <Row gutter={24}>
        {/* Left Panel - Strategy Documentation */}
        <Col xs={24} lg={8}>
          <Card
            title="📚 策略文档"
            style={{ position: 'sticky', top: 16, maxHeight: 'calc(100vh - 100px)', overflowY: 'auto' }}
          >
            {/* Search Box */}
            <Input
              placeholder="搜索策略..."
              prefix={<SearchOutlined />}
              value={strategySearch}
              onChange={(e) => setStrategySearch(e.target.value)}
              style={{ marginBottom: 16 }}
              allowClear
            />

            {strategies.length === 0 ? (
              <Spin />
            ) : (
              <div>
                {strategies
                  .filter(strategy =>
                    strategy.name.toLowerCase().includes(strategySearch.toLowerCase()) ||
                    strategy.description.toLowerCase().includes(strategySearch.toLowerCase())
                  )
                  .map((strategy) => {
                    const isSelected = selectedStrategies.includes(strategy.id);
                    return (
                      <div
                        key={strategy.id}
                        style={{
                          padding: isSelected ? 16 : 12,
                          marginBottom: 8,
                          borderRadius: 8,
                          border: isSelected ? '2px solid #1890ff' : '1px solid #e8e8e8',
                          backgroundColor: isSelected ? '#e6f7ff' : '#fff',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                        }}
                        onClick={() => handleStrategyToggle(strategy.id)}
                        onMouseEnter={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.borderColor = '#d9d9d9';
                            e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.05)';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.borderColor = '#e8e8e8';
                            e.currentTarget.style.boxShadow = 'none';
                          }
                        }}
                      >
                        {/* Strategy Header */}
                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                          <Title level={5} style={{ margin: 0, flex: 1, fontSize: isSelected ? 15 : 14 }}>
                            {strategy.name}
                          </Title>
                          <FileTextOutlined
                            style={{
                              color: '#1890ff',
                              fontSize: 16,
                              cursor: 'pointer',
                              marginRight: 8,
                            }}
                            onClick={(e) => handleViewDocumentation(strategy.id, e)}
                            title="查看详细文档"
                          />
                          {isSelected && (
                            <CheckCircleOutlined style={{ color: '#1890ff', fontSize: 16 }} />
                          )}
                        </div>

                        {/* Strategy Description - Always visible but compact */}
                        <Text
                          style={{
                            fontSize: 12,
                            color: '#8c8c8c',
                            display: 'block',
                            marginTop: 4,
                          }}
                        >
                          {strategy.description}
                        </Text>
                      </div>
                    );
                  })}

                {/* No results message */}
                {strategies.filter(s =>
                  s.name.toLowerCase().includes(strategySearch.toLowerCase()) ||
                  s.description.toLowerCase().includes(strategySearch.toLowerCase())
                ).length === 0 && (
                  <div style={{ textAlign: 'center', padding: 40, color: '#bfbfbf' }}>
                    <SearchOutlined style={{ fontSize: 32, marginBottom: 8 }} />
                    <div>未找到匹配的策略</div>
                  </div>
                )}
              </div>
            )}
          </Card>
        </Col>

        {/* Right Panel - Backtest Form */}
        <Col xs={24} lg={16}>
          <Card>
            <Title level={4} style={{ marginTop: 0 }}>
              回测配置
            </Title>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            symbol: '01810.HK',
            timeRange: '3m',
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
              <Form.Item label="已选择策略">
                <div style={{
                  padding: '8px 12px',
                  backgroundColor: selectedStrategies.length > 0 ? '#e6f7ff' : '#fafafa',
                  border: `1px solid ${selectedStrategies.length > 0 ? '#1890ff' : '#d9d9d9'}`,
                  borderRadius: 6,
                  minHeight: 32,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  {selectedStrategies.length === 0 ? (
                    <Text type="secondary">请从左侧选择策略</Text>
                  ) : (
                    <Text strong style={{ color: '#1890ff' }}>
                      已选择 {selectedStrategies.length} 个策略
                    </Text>
                  )}
                </div>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="回测时间区间"
                name="timeRange"
                rules={[{ required: true, message: '请选择回测时间区间' }]}
              >
                <Select placeholder="选择时间区间">
                  {TIME_RANGES.map(range => (
                    <Select.Option key={range.value} value={range.value}>
                      {range.label}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          {/* Strategy Parameters - Show each strategy's parameters separately */}
          {selectedStrategies.length > 0 && selectedStrategies.map(strategyId => {
            const strategy = strategies.find(s => s.id === strategyId);
            if (!strategy || strategy.parameters.length === 0) return null;

            return (
              <Row gutter={16} style={{ marginTop: 8 }} key={strategyId}>
                <Col span={24}>
                  <div style={{
                    padding: 16,
                    backgroundColor: '#fafafa',
                    borderRadius: 8,
                    marginBottom: 16,
                    border: '1px solid #d9d9d9'
                  }}>
                    <Text strong style={{ fontSize: 14 }}>
                      {strategy.name} - 参数设置
                    </Text>
                    <Row gutter={16} style={{ marginTop: 12 }}>
                      {strategy.parameters.map((param) => (
                        <Col xs={24} md={8} key={param.name}>
                          <Form.Item
                            label={param.label}
                            name={`param_${strategyId}_${param.name}`}
                            tooltip={param.description}
                            initialValue={param.default}
                            valuePropName={param.type === 'boolean' ? 'checked' : 'value'}
                          >
                            <ParameterInput parameter={param} />
                          </Form.Item>
                        </Col>
                      ))}
                    </Row>
                  </div>
                </Col>
              </Row>
            );
          })}

          {/* Strategy Combination Settings - Show only when multiple strategies selected */}
          {selectedStrategies.length > 1 && (
            <Row gutter={16} style={{ marginTop: 8 }}>
              <Col span={24}>
                <div style={{
                  padding: 16,
                  backgroundColor: '#fff7e6',
                  borderRadius: 8,
                  marginBottom: 16,
                  border: '1px solid #ffd591'
                }}>
                  <Text strong style={{ fontSize: 14, color: '#d46b08' }}>策略组合设置</Text>
                  <Row gutter={16} style={{ marginTop: 12 }}>
                    <Col xs={24} md={12}>
                      <Form.Item
                        label="组合模式"
                        name="combineMode"
                        tooltip="选择多个策略时如何组合它们的信号"
                        initialValue="AND"
                      >
                        <Select>
                          <Select.Option value="AND">AND - 所有策略同时确认</Select.Option>
                          <Select.Option value="OR">OR - 任一策略触发</Select.Option>
                          <Select.Option value="VOTE">VOTE - 投票机制</Select.Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col xs={24} md={12}>
                      <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.combineMode !== currentValues.combineMode}>
                        {({ getFieldValue }) => {
                          const combineMode = getFieldValue('combineMode');
                          return combineMode === 'VOTE' ? (
                            <Form.Item
                              label="投票阈值"
                              name="voteThreshold"
                              tooltip="需要多少个策略发出信号才执行交易"
                              initialValue={Math.ceil(selectedStrategies.length / 2)}
                            >
                              <InputNumber
                                style={{ width: '100%' }}
                                min={1}
                                max={selectedStrategies.length}
                                addonAfter={`/ ${selectedStrategies.length}`}
                              />
                            </Form.Item>
                          ) : (
                            <div style={{ paddingTop: 30, color: '#8c8c8c', fontSize: 12 }}>
                              {combineMode === 'AND' && '所有策略必须同时发出信号才会执行交易'}
                              {combineMode === 'OR' && '任何一个策略发出信号即可执行交易'}
                            </div>
                          );
                        }}
                      </Form.Item>
                    </Col>
                  </Row>
                </div>
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
                  disabled={selectedStrategies.length === 0}
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

      {(() => {
        console.log('Render check - result:', !!result, 'loading:', loading, 'selectedStrategies:', selectedStrategies.length);
        return null;
      })()}

      {result && !loading && (
        <>
          {/* Strategy Info */}
          {selectedStrategies.length > 0 && (
            <Card style={{ marginTop: 24, backgroundColor: '#fafafa' }}>
              <Row align="middle" gutter={16}>
                <Col>
                  <Text strong style={{ fontSize: 14 }}>使用策略:</Text>
                </Col>
                <Col flex="auto">
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {selectedStrategies.map(strategyId => {
                      const strategy = strategies.find(s => s.id === strategyId);
                      return strategy ? (
                        <div
                          key={strategyId}
                          style={{
                            padding: '4px 12px',
                            backgroundColor: '#1890ff',
                            color: 'white',
                            borderRadius: 4,
                            fontSize: 13,
                          }}
                        >
                          {strategy.name}
                        </div>
                      ) : null;
                    })}
                  </div>
                </Col>
                {selectedStrategies.length > 1 && (
                  <Col>
                    <Text style={{ fontSize: 13, color: '#8c8c8c' }}>
                      组合模式: <Text strong style={{ color: '#d46b08' }}>
                        {form.getFieldValue('combineMode') === 'AND' && 'AND (全部确认)'}
                        {form.getFieldValue('combineMode') === 'OR' && 'OR (任一触发)'}
                        {form.getFieldValue('combineMode') === 'VOTE' && `VOTE (${form.getFieldValue('voteThreshold')}/${selectedStrategies.length})`}
                      </Text>
                    </Text>
                  </Col>
                )}
              </Row>
            </Card>
          )}

          {/* Results Statistics */}
          <Card title="📊 回测结果" style={{ marginTop: 24 }}>
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

          {/* Signal Analysis - Current Market Position */}
          {result.signal_analysis && (
            <SignalAnalysisCard signalAnalysis={result.signal_analysis} />
          )}

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
          <Card title="📋 交易明细" style={{ marginTop: 24 }}>
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
        </Col>
      </Row>

      {/* Strategy Documentation Modal */}
      <StrategyDocModal
        strategyId={currentDocStrategyId}
        open={docModalOpen}
        onClose={() => setDocModalOpen(false)}
      />
    </div>
  );
}
