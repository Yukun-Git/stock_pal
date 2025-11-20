import { useEffect, useState } from 'react';
import { Modal, Spin, Alert, Typography, Tag, Space } from 'antd';
import { BulbOutlined, RobotOutlined, ClockCircleOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { aiApi } from '@/services/api';

const { Title, Text } = Typography;

interface AIAnalysisModalProps {
  open: boolean;
  onClose: () => void;
  backtestData: {
    stock_info: {
      symbol: string;
      name: string;
      period: string;
    };
    strategy_info: {
      name: string;
      description: string;
    };
    parameters: {
      initial_capital: number;
      commission_rate: number;
      strategy_params?: Record<string, any>;
    };
    backtest_results: {
      total_return: number;
      win_rate: number;
      max_drawdown: number;
      profit_factor: number;
      total_trades: number;
      winning_trades: number;
      losing_trades: number;
    };
  } | null;
}

export default function AIAnalysisModal({ open, onClose, backtestData }: AIAnalysisModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<{
    model: string;
    tokens_used: number;
    analysis_time: number;
  } | null>(null);

  useEffect(() => {
    if (open && backtestData) {
      analyzeBacktest();
    }
  }, [open, backtestData]);

  const analyzeBacktest = async () => {
    if (!backtestData) return;

    setLoading(true);
    setError(null);
    setAnalysis(null);
    setMetadata(null);

    try {
      const result = await aiApi.analyzeBacktest(backtestData);
      setAnalysis(result.analysis);
      setMetadata({
        model: result.model,
        tokens_used: result.tokens_used,
        analysis_time: result.analysis_time,
      });
    } catch (err: any) {
      const status = err?.response?.status;
      const errorMessage = err?.response?.data?.error;

      if (status === 503) {
        setError('AI分析服务暂未配置。请联系管理员配置阿里云通义千问API密钥。');
      } else if (errorMessage) {
        setError(errorMessage);
      } else {
        setError('AI分析失败，请稍后重试');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <BulbOutlined style={{ color: '#faad14' }} />
          <span>AI智能分析</span>
        </div>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width={900}
      style={{ top: 20 }}
      bodyStyle={{ maxHeight: 'calc(100vh - 200px)', overflowY: 'auto' }}
    >
      {loading && (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" tip="AI正在分析中，请稍候..." />
          <div style={{ marginTop: 16, color: '#8c8c8c' }}>
            <Text type="secondary">正在使用阿里云通义千问AI分析您的回测结果...</Text>
          </div>
        </div>
      )}

      {error && (
        <Alert
          message="分析失败"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {!loading && !error && analysis && (
        <div>
          {metadata && (
            <div style={{ marginBottom: 24, padding: 12, background: '#f5f5f5', borderRadius: 6 }}>
              <Space size="large">
                <Space>
                  <RobotOutlined style={{ color: '#1890ff' }} />
                  <Text type="secondary">模型: {metadata.model}</Text>
                </Space>
                <Space>
                  <ClockCircleOutlined style={{ color: '#52c41a' }} />
                  <Text type="secondary">分析用时: {metadata.analysis_time.toFixed(2)}秒</Text>
                </Space>
                <Tag color="blue">Tokens: {metadata.tokens_used}</Tag>
              </Space>
            </div>
          )}

          <div className="ai-analysis-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ node, ...props }) => (
                  <Title level={2} style={{ marginTop: 24, marginBottom: 16 }} {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <Title level={3} style={{ marginTop: 20, marginBottom: 12, color: '#1890ff' }} {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <Title level={4} style={{ marginTop: 16, marginBottom: 8 }} {...props} />
                ),
                table: ({ node, ...props }) => (
                  <div style={{ overflowX: 'auto', marginBottom: 16 }}>
                    <table
                      style={{
                        width: '100%',
                        borderCollapse: 'collapse',
                        border: '1px solid #e8e8e8',
                      }}
                      {...props}
                    />
                  </div>
                ),
                thead: ({ node, ...props }) => (
                  <thead style={{ backgroundColor: '#fafafa' }} {...props} />
                ),
                th: ({ node, ...props }) => (
                  <th
                    style={{
                      padding: '12px 16px',
                      textAlign: 'left',
                      borderBottom: '2px solid #e8e8e8',
                      borderRight: '1px solid #e8e8e8',
                      fontWeight: 600,
                    }}
                    {...props}
                  />
                ),
                td: ({ node, ...props }) => (
                  <td
                    style={{
                      padding: '12px 16px',
                      borderBottom: '1px solid #e8e8e8',
                      borderRight: '1px solid #e8e8e8',
                    }}
                    {...props}
                  />
                ),
                ul: ({ node, ...props }) => (
                  <ul style={{ paddingLeft: 24, marginBottom: 16 }} {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol style={{ paddingLeft: 24, marginBottom: 16 }} {...props} />
                ),
                li: ({ node, ...props }) => (
                  <li style={{ marginBottom: 8 }} {...props} />
                ),
                p: ({ node, ...props }) => (
                  <p style={{ marginBottom: 12, lineHeight: 1.8 }} {...props} />
                ),
                code: ({ node, inline, ...props }: any) => {
                  if (inline) {
                    return (
                      <code
                        style={{
                          backgroundColor: '#f5f5f5',
                          padding: '2px 6px',
                          borderRadius: 3,
                          fontSize: '0.9em',
                          fontFamily: 'Consolas, Monaco, monospace',
                        }}
                        {...props}
                      />
                    );
                  }
                  return (
                    <code
                      style={{
                        display: 'block',
                        backgroundColor: '#f5f5f5',
                        padding: 16,
                        borderRadius: 6,
                        fontSize: '0.9em',
                        fontFamily: 'Consolas, Monaco, monospace',
                        overflowX: 'auto',
                        marginBottom: 16,
                      }}
                      {...props}
                    />
                  );
                },
                blockquote: ({ node, ...props }) => (
                  <blockquote
                    style={{
                      borderLeft: '4px solid #faad14',
                      paddingLeft: 16,
                      marginLeft: 0,
                      marginBottom: 16,
                      color: '#595959',
                      fontStyle: 'italic',
                    }}
                    {...props}
                  />
                ),
                strong: ({ node, ...props }) => (
                  <strong style={{ color: '#262626', fontWeight: 600 }} {...props} />
                ),
              }}
            >
              {analysis}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </Modal>
  );
}
