import { useState } from 'react';
import { Card, Row, Col, Button, Collapse, Slider, Switch, Typography, Tooltip } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';
import type { RiskConfig, RiskTemplate } from '@/types';

const { Text } = Typography;

interface RiskConfigPanelProps {
  value?: RiskConfig | null;
  onChange?: (config: RiskConfig | null) => void;
  onOpenHelp?: () => void;  // 新增：打开帮助文档的回调
}

// 预设模板
const RISK_TEMPLATES: Record<RiskTemplate, RiskConfig | null> = {
  conservative: {
    stop_loss_pct: 0.08,
    stop_profit_pct: 0.15,
    max_drawdown_pct: 0.15,
    max_position_pct: 0.20,
    max_total_exposure: 0.95,
  },
  balanced: {
    stop_loss_pct: 0.10,
    stop_profit_pct: 0.20,
    max_drawdown_pct: 0.20,
    max_position_pct: 0.30,
    max_total_exposure: 0.95,
  },
  aggressive: {
    stop_loss_pct: 0.15,
    stop_profit_pct: 0.30,
    max_drawdown_pct: 0.25,
    max_position_pct: 0.50,
    max_total_exposure: 0.95,
  },
  custom: null,
  null: null,
};

const TEMPLATE_INFO = {
  conservative: {
    icon: '🛡️',
    name: '保守型',
    description: '适合风险厌恶型投资者，严格控制风险',
  },
  balanced: {
    icon: '⚖️',
    name: '平衡型',
    description: '平衡风险与收益，适合大多数投资者',
  },
  aggressive: {
    icon: '🚀',
    name: '激进型',
    description: '追求高收益，承受较高风险',
  },
};

export default function RiskConfigPanel({ value, onChange, onOpenHelp }: RiskConfigPanelProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<RiskTemplate>('balanced');
  const [customConfig, setCustomConfig] = useState<RiskConfig>({
    stop_loss_pct: 0.10,
    stop_profit_pct: 0.20,
    max_drawdown_pct: 0.20,
    max_position_pct: 0.30,
    max_total_exposure: 0.95,
  });
  const [enableStopLoss, setEnableStopLoss] = useState(true);
  const [enableStopProfit, setEnableStopProfit] = useState(true);
  const [enableDrawdownProtection, setEnableDrawdownProtection] = useState(true);

  // 处理模板选择
  const handleTemplateSelect = (template: RiskTemplate) => {
    setSelectedTemplate(template);
    if (template === null) {
      onChange?.(null);
    } else if (template === 'custom') {
      onChange?.(customConfig);
    } else {
      const config = RISK_TEMPLATES[template];
      onChange?.(config);
    }
  };

  // 处理自定义配置变化
  const handleCustomConfigChange = (key: keyof RiskConfig, val: number | null) => {
    const newConfig = { ...customConfig, [key]: val };
    setCustomConfig(newConfig);
    if (selectedTemplate === 'custom') {
      onChange?.(newConfig);
    }
  };

  // 恢复默认配置
  const handleRestoreDefault = () => {
    const balancedConfig = RISK_TEMPLATES.balanced!;
    setCustomConfig(balancedConfig);
    setSelectedTemplate('balanced');
    setEnableStopLoss(true);
    setEnableStopProfit(true);
    setEnableDrawdownProtection(true);
    onChange?.(balancedConfig);
  };

  return (
    <Card
      title={
        <span>
          风控配置
          <Tooltip title="点击查看风控详细说明">
            <QuestionCircleOutlined
              style={{ marginLeft: 8, color: '#1890ff', fontSize: 14, cursor: 'pointer' }}
              onClick={onOpenHelp}
            />
          </Tooltip>
        </span>
      }
    >
      <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
        选择风控模板：
      </Text>

      {/* 模板选择卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {(Object.keys(TEMPLATE_INFO) as Array<keyof typeof TEMPLATE_INFO>).map((template) => {
          const info = TEMPLATE_INFO[template];
          const config = RISK_TEMPLATES[template];
          const isSelected = selectedTemplate === template;

          return (
            <Col xs={24} sm={8} key={template}>
              <div
                onClick={() => handleTemplateSelect(template)}
                style={{
                  padding: 16,
                  borderRadius: 8,
                  border: isSelected ? '2px solid #1890ff' : '1px solid #d9d9d9',
                  backgroundColor: isSelected ? '#e6f7ff' : '#fff',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  textAlign: 'center',
                  minHeight: 160,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.borderColor = '#40a9ff';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.borderColor = '#d9d9d9';
                    e.currentTarget.style.boxShadow = 'none';
                  }
                }}
              >
                <div style={{ fontSize: 32, marginBottom: 8 }}>{info.icon}</div>
                <Text strong style={{ fontSize: 16, display: 'block', marginBottom: 4 }}>
                  {info.name}
                </Text>
                {isSelected && (
                  <Text type="secondary" style={{ fontSize: 12, color: '#1890ff' }}>
                    [已选中]
                  </Text>
                )}
                <div style={{ marginTop: 12, fontSize: 12, color: '#8c8c8c' }}>
                  <div>止损 {config && ((config.stop_loss_pct || 0) * 100).toFixed(0)}%</div>
                  <div>止盈 {config && ((config.stop_profit_pct || 0) * 100).toFixed(0)}%</div>
                  <div>回撤 {config && ((config.max_drawdown_pct || 0) * 100).toFixed(0)}%</div>
                  <div>仓位 {config && ((config.max_position_pct || 0) * 100).toFixed(0)}%</div>
                </div>
              </div>
            </Col>
          );
        })}
      </Row>

      {/* 自定义配置折叠面板 */}
      <Collapse
        ghost
        items={[
          {
            key: 'custom',
            label: '自定义配置',
            children: (
              <div style={{ padding: '16px 0' }}>
                {/* 止损止盈 */}
                <div style={{ marginBottom: 24 }}>
                  <Text strong style={{ display: 'block', marginBottom: 12 }}>
                    止损止盈
                  </Text>

                  <Row gutter={16} style={{ marginBottom: 12 }}>
                    <Col span={18}>
                      <Text type="secondary" style={{ fontSize: 12 }}>止损线</Text>
                      <Slider
                        value={(customConfig.stop_loss_pct || 0) * 100}
                        onChange={(val) => handleCustomConfigChange('stop_loss_pct', enableStopLoss ? val / 100 : null)}
                        min={5}
                        max={30}
                        step={1}
                        marks={{ 5: '5%', 10: '10%', 15: '15%', 20: '20%', 30: '30%' }}
                        disabled={!enableStopLoss}
                      />
                    </Col>
                    <Col span={6}>
                      <Switch
                        checked={enableStopLoss}
                        onChange={(checked) => {
                          setEnableStopLoss(checked);
                          if (!checked) {
                            handleCustomConfigChange('stop_loss_pct', null);
                          } else {
                            handleCustomConfigChange('stop_loss_pct', 0.10);
                          }
                        }}
                        checkedChildren="启用"
                        unCheckedChildren="禁用"
                      />
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={18}>
                      <Text type="secondary" style={{ fontSize: 12 }}>止盈线</Text>
                      <Slider
                        value={(customConfig.stop_profit_pct || 0) * 100}
                        onChange={(val) => handleCustomConfigChange('stop_profit_pct', enableStopProfit ? val / 100 : null)}
                        min={10}
                        max={50}
                        step={5}
                        marks={{ 10: '10%', 20: '20%', 30: '30%', 40: '40%', 50: '50%' }}
                        disabled={!enableStopProfit}
                      />
                    </Col>
                    <Col span={6}>
                      <Switch
                        checked={enableStopProfit}
                        onChange={(checked) => {
                          setEnableStopProfit(checked);
                          if (!checked) {
                            handleCustomConfigChange('stop_profit_pct', null);
                          } else {
                            handleCustomConfigChange('stop_profit_pct', 0.20);
                          }
                        }}
                        checkedChildren="启用"
                        unCheckedChildren="禁用"
                      />
                    </Col>
                  </Row>
                </div>

                {/* 仓位控制 */}
                <div style={{ marginBottom: 24 }}>
                  <Text strong style={{ display: 'block', marginBottom: 12 }}>
                    仓位控制
                  </Text>

                  <Row gutter={16} style={{ marginBottom: 12 }}>
                    <Col span={24}>
                      <Text type="secondary" style={{ fontSize: 12 }}>单票仓位</Text>
                      <Slider
                        value={(customConfig.max_position_pct || 0) * 100}
                        onChange={(val) => handleCustomConfigChange('max_position_pct', val / 100)}
                        min={10}
                        max={100}
                        step={5}
                        marks={{ 10: '10%', 30: '30%', 50: '50%', 70: '70%', 100: '100%' }}
                      />
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={24}>
                      <Text type="secondary" style={{ fontSize: 12 }}>总仓位</Text>
                      <Slider
                        value={(customConfig.max_total_exposure || 0) * 100}
                        onChange={(val) => handleCustomConfigChange('max_total_exposure', val / 100)}
                        min={50}
                        max={100}
                        step={5}
                        marks={{ 50: '50%', 70: '70%', 90: '90%', 100: '100%' }}
                      />
                    </Col>
                  </Row>
                </div>

                {/* 组合风控 */}
                <div style={{ marginBottom: 16 }}>
                  <Text strong style={{ display: 'block', marginBottom: 12 }}>
                    组合风控
                  </Text>

                  <Row gutter={16}>
                    <Col span={18}>
                      <Text type="secondary" style={{ fontSize: 12 }}>回撤保护</Text>
                      <Slider
                        value={(customConfig.max_drawdown_pct || 0) * 100}
                        onChange={(val) => handleCustomConfigChange('max_drawdown_pct', enableDrawdownProtection ? val / 100 : null)}
                        min={10}
                        max={40}
                        step={5}
                        marks={{ 10: '10%', 20: '20%', 30: '30%', 40: '40%' }}
                        disabled={!enableDrawdownProtection}
                      />
                    </Col>
                    <Col span={6}>
                      <Switch
                        checked={enableDrawdownProtection}
                        onChange={(checked) => {
                          setEnableDrawdownProtection(checked);
                          if (!checked) {
                            handleCustomConfigChange('max_drawdown_pct', null);
                          } else {
                            handleCustomConfigChange('max_drawdown_pct', 0.20);
                          }
                        }}
                        checkedChildren="启用"
                        unCheckedChildren="禁用"
                      />
                    </Col>
                  </Row>
                </div>

                {/* 操作按钮 */}
                <Row justify="space-between" style={{ marginTop: 24 }}>
                  <Col>
                    <Button onClick={handleRestoreDefault}>恢复默认</Button>
                  </Col>
                  <Col>
                    <Button
                      type="primary"
                      onClick={() => {
                        setSelectedTemplate('custom');
                        onChange?.(customConfig);
                      }}
                    >
                      应用自定义配置
                    </Button>
                  </Col>
                </Row>
              </div>
            ),
          },
        ]}
      />

      {/* 不启用风控选项 */}
      <div style={{ marginTop: 16, textAlign: 'center' }}>
        <Button
          type="link"
          danger
          onClick={() => handleTemplateSelect(null)}
          style={{ fontSize: 12 }}
        >
          不启用风控
        </Button>
      </div>
    </Card>
  );
}
