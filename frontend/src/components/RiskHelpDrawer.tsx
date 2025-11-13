import { Drawer, Typography, Divider } from 'antd';

const { Title, Text, Paragraph } = Typography;

interface RiskHelpDrawerProps {
  open: boolean;
  onClose: () => void;
}

export default function RiskHelpDrawer({ open, onClose }: RiskHelpDrawerProps) {
  return (
    <Drawer
      title="风控管理 - 帮助文档"
      placement="right"
      onClose={onClose}
      open={open}
      width={560}
    >
      {/* 什么是风控 */}
      <Title level={4}>📖 什么是风控？</Title>
      <Paragraph>
        风控（风险控制）是一套规则，在回测或实盘中自动执行，
        帮助你控制亏损、锁定收益、防止账户大幅回撤。
      </Paragraph>

      <Divider />

      {/* 止损 */}
      <Title level={4}>🛡️ 止损</Title>
      <Paragraph>
        <Text strong>定义：</Text>股价亏损超过设定比例时自动卖出
      </Paragraph>
      <Paragraph>
        <Text strong>例子：</Text>设置止损-10%，买入价10元，跌至9元时自动卖出
      </Paragraph>
      <Paragraph>
        <Text strong>作用：</Text>避免深度套牢，控制单笔亏损
      </Paragraph>
      <div style={{ padding: 12, backgroundColor: '#fff7e6', borderRadius: 6, marginBottom: 16 }}>
        <Text style={{ fontSize: 12, color: '#d46b08' }}>
          💡 <strong>止损建议：</strong>
          <br />
          • 5-8%：短线交易
          <br />
          • 10-15%：中线波段（推荐）
          <br />
          • 20%+：长线持有
          <br />
          <br />
          注意：止损线太紧容易频繁触发，太松则保护作用有限
        </Text>
      </div>

      <Divider />

      {/* 止盈 */}
      <Title level={4}>💰 止盈</Title>
      <Paragraph>
        <Text strong>定义：</Text>股价盈利超过设定比例时自动卖出
      </Paragraph>
      <Paragraph>
        <Text strong>例子：</Text>设置止盈+20%，买入价10元，涨至12元时自动卖出
      </Paragraph>
      <Paragraph>
        <Text strong>作用：</Text>锁定利润，避免回吐收益
      </Paragraph>
      <div style={{ padding: 12, backgroundColor: '#f6ffed', borderRadius: 6, marginBottom: 16 }}>
        <Text style={{ fontSize: 12, color: '#52c41a' }}>
          💡 <strong>止盈建议：</strong>
          <br />
          • 10-15%：短线快进快出
          <br />
          • 20-30%：中线获利了结（推荐）
          <br />
          • 50%+：长线价值投资
          <br />
          <br />
          注意：止盈不应设置得太低，否则可能错失大行情
        </Text>
      </div>

      <Divider />

      {/* 回撤保护 */}
      <Title level={4}>⚠️ 回撤保护</Title>
      <Paragraph>
        <Text strong>定义：</Text>账户从最高点回撤超过设定比例时清空所有持仓
      </Paragraph>
      <Paragraph>
        <Text strong>例子：</Text>设置回撤20%，权益最高14万，跌至11.2万时清仓
      </Paragraph>
      <Paragraph>
        <Text strong>作用：</Text>在系统性下跌中保护本金
      </Paragraph>
      <div style={{ padding: 12, backgroundColor: '#fff1f0', borderRadius: 6, marginBottom: 16 }}>
        <Text style={{ fontSize: 12, color: '#f5222d' }}>
          💡 <strong>回撤保护建议：</strong>
          <br />
          • 15-20%：较为保守，适合熊市
          <br />
          • 20-25%：平衡型（推荐）
          <br />
          • 30%+：较为激进，容忍更大回撤
          <br />
          <br />
          注意：回撤保护是"最后一道防线"，触发后会清空所有持仓
        </Text>
      </div>

      <Divider />

      {/* 仓位限制 */}
      <Title level={4}>🔢 仓位限制</Title>
      <Paragraph>
        <Text strong>定义：</Text>限制单只股票或总持仓占资金的比例
      </Paragraph>
      <Paragraph>
        <Text strong>例子：</Text>单票仓位30%，10万资金最多买3万元一只股票
      </Paragraph>
      <Paragraph>
        <Text strong>作用：</Text>分散风险，避免重仓一只股票
      </Paragraph>
      <div style={{ padding: 12, backgroundColor: '#f0f5ff', borderRadius: 6, marginBottom: 16 }}>
        <Text style={{ fontSize: 12, color: '#1890ff' }}>
          💡 <strong>仓位限制建议：</strong>
          <br />
          • 单票仓位 20-30%：分散风险
          <br />
          • 单票仓位 50%+：集中投资（高风险）
          <br />
          • 总仓位 95%：保留少量现金应对波动
          <br />
          <br />
          注意：不要把所有资金投入单只股票，"鸡蛋不要放在一个篮子里"
        </Text>
      </div>

      <Divider />

      {/* 综合建议 */}
      <Title level={4}>🎯 综合建议</Title>
      <Paragraph>
        <Text strong>新手用户：</Text>推荐使用"平衡型"模板，风险收益平衡
      </Paragraph>
      <Paragraph>
        <Text strong>进阶用户：</Text>可以根据自己的风险承受能力调整参数
      </Paragraph>
      <Paragraph>
        <Text strong>重要提示：</Text>
      </Paragraph>
      <ul style={{ paddingLeft: 20, marginTop: 8 }}>
        <li>风控是辅助工具，策略选择更重要</li>
        <li>不要频繁调整参数，避免过度优化</li>
        <li>回测结果不代表未来收益，请谨慎对待</li>
        <li>风控不能保证100%避免亏损</li>
      </ul>

      <div style={{ marginTop: 24, padding: 16, backgroundColor: '#fafafa', borderRadius: 8 }}>
        <Text style={{ fontSize: 13, color: '#595959' }}>
          💬 <strong>提示：</strong>通过"查看详细对比"功能，你可以直观地看到风控对回测结果的影响。
          建议多尝试不同的风控配置，找到最适合自己的参数组合。
        </Text>
      </div>
    </Drawer>
  );
}
