import { useState, useEffect } from 'react';
import { Modal, Button, Typography, Steps } from 'antd';

const { Title, Text, Paragraph } = Typography;

interface RiskOnboardingProps {
  onComplete: () => void;
  skip?: boolean;
}

export default function RiskOnboarding({ onComplete, skip = false }: RiskOnboardingProps) {
  const [open, setOpen] = useState(!skip);
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (skip) {
      setOpen(false);
    }
  }, [skip]);

  const steps = [
    {
      title: '欢迎使用风控管理',
      icon: '🎉',
      content: (
        <div>
          <Title level={4} style={{ marginTop: 0 }}>风控可以帮助你：</Title>
          <div style={{ paddingLeft: 16 }}>
            <Paragraph>
              ✓ 自动止损，避免深度套牢
            </Paragraph>
            <Paragraph>
              ✓ 自动止盈，锁定利润
            </Paragraph>
            <Paragraph>
              ✓ 回撤保护，防止账户大幅亏损
            </Paragraph>
          </div>
          <Title level={4}>我们为你准备了3种预设模板：</Title>
          <div style={{ paddingLeft: 16 }}>
            <Paragraph>
              • <Text strong>保守型：</Text>适合新手，风控较严格
            </Paragraph>
            <Paragraph>
              • <Text strong>平衡型：</Text>推荐使用，风险收益平衡
            </Paragraph>
            <Paragraph>
              • <Text strong>激进型：</Text>追求高收益，风控较宽松
            </Paragraph>
          </div>
        </div>
      ),
    },
    {
      title: '如何配置风控',
      icon: '⚙️',
      content: (
        <div>
          <Paragraph>
            在回测配置页面，你会看到<Text strong>"风控配置"</Text>面板。
          </Paragraph>
          <Paragraph>
            点击模板卡片可以快速应用预设配置，也可以展开<Text strong>"自定义配置"</Text>进行精细调整。
          </Paragraph>
          <div style={{ padding: 16, backgroundColor: '#f0f5ff', borderRadius: 8, marginTop: 16 }}>
            <Text style={{ fontSize: 13, color: '#1890ff' }}>
              💡 <strong>提示：</strong>首次使用推荐选择"平衡型"模板，体验风控的效果。
            </Text>
          </div>
        </div>
      ),
    },
    {
      title: '查看风控效果',
      icon: '📊',
      content: (
        <div>
          <Paragraph>
            回测完成后，你可以在结果页面看到<Text strong>"风控影响分析"</Text>卡片，
            显示止损、止盈、回撤保护的触发次数和效果。
          </Paragraph>
          <Paragraph>
            点击<Text strong>"查看详细对比"</Text>按钮，可以查看有/无风控的详细对比分析。
          </Paragraph>
          <div style={{ padding: 16, backgroundColor: '#fff7e6', borderRadius: 8, marginTop: 16 }}>
            <Text style={{ fontSize: 13, color: '#d46b08' }}>
              💡 <strong>提示：</strong>K线图上会用不同颜色标注风控触发点，帮助你理解风控的作用。
            </Text>
          </div>
        </div>
      ),
    },
    {
      title: '开始体验',
      icon: '✅',
      content: (
        <div>
          <Paragraph>
            你已经了解了风控功能的基本用法！
          </Paragraph>
          <Paragraph>
            接下来，试试对比有/无风控的回测结果，看看风控能为你的策略带来什么改变。
          </Paragraph>
          <div style={{ padding: 16, backgroundColor: '#f6ffed', borderRadius: 8, marginTop: 16 }}>
            <Text style={{ fontSize: 13, color: '#52c41a' }}>
              💡 <strong>小贴士：</strong>
              <br />
              • 风控是辅助工具，策略选择更重要
              <br />
              • 不要频繁调整参数，避免过度优化
              <br />
              • 随时可以点击"?"图标查看帮助文档
            </Text>
          </div>
        </div>
      ),
    },
  ];

  const handleNext = () => {
    if (current < steps.length - 1) {
      setCurrent(current + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrev = () => {
    if (current > 0) {
      setCurrent(current - 1);
    }
  };

  const handleSkip = () => {
    setOpen(false);
    onComplete();
  };

  const handleComplete = () => {
    setOpen(false);
    onComplete();
    // 可以在这里保存到 localStorage，避免重复显示
    localStorage.setItem('risk_onboarding_completed', 'true');
  };

  return (
    <Modal
      open={open}
      title={null}
      footer={null}
      closable={false}
      width={600}
      centered
    >
      <div style={{ padding: '24px 0' }}>
        {/* 步骤指示器 */}
        <Steps
          current={current}
          items={steps.map((step) => ({
            title: step.title,
          }))}
          size="small"
          style={{ marginBottom: 32 }}
        />

        {/* 当前步骤内容 */}
        <div style={{ minHeight: 300 }}>
          <div style={{ fontSize: 48, textAlign: 'center', marginBottom: 16 }}>
            {steps[current].icon}
          </div>
          <Title level={3} style={{ textAlign: 'center', marginBottom: 24 }}>
            {steps[current].title}
          </Title>
          {steps[current].content}
        </div>

        {/* 按钮组 */}
        <div style={{ marginTop: 32, display: 'flex', justifyContent: 'space-between' }}>
          <div>
            {current === 0 && (
              <Button onClick={handleSkip}>
                跳过
              </Button>
            )}
            {current > 0 && (
              <Button onClick={handlePrev}>
                上一步
              </Button>
            )}
          </div>
          <Button type="primary" onClick={handleNext}>
            {current === steps.length - 1 ? '开始使用' : '下一步'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// 辅助函数：检查是否需要显示引导
export function shouldShowOnboarding(): boolean {
  return localStorage.getItem('risk_onboarding_completed') !== 'true';
}

// 辅助函数：重置引导状态（用于测试）
export function resetOnboarding(): void {
  localStorage.removeItem('risk_onboarding_completed');
}
