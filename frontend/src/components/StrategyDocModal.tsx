import { useEffect, useState } from 'react';
import { Modal, Spin, Alert, Typography } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { strategyApi } from '@/services/api';
import type { StrategyDocumentation } from '@/types';

const { Title } = Typography;

interface StrategyDocModalProps {
  strategyId: string | null;
  open: boolean;
  onClose: () => void;
}

export default function StrategyDocModal({ strategyId, open, onClose }: StrategyDocModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentation, setDocumentation] = useState<StrategyDocumentation | null>(null);

  useEffect(() => {
    if (open && strategyId) {
      loadDocumentation();
    }
  }, [open, strategyId]);

  const loadDocumentation = async () => {
    if (!strategyId) return;

    setLoading(true);
    setError(null);

    try {
      const doc = await strategyApi.getStrategyDocumentation(strategyId);
      setDocumentation(doc);
    } catch (err: any) {
      setError(err?.response?.data?.error || '加载策略文档失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <FileTextOutlined />
          <span>{documentation?.strategy_name || '策略文档'}</span>
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
          <Spin size="large" tip="加载文档中..." />
        </div>
      )}

      {error && (
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
        />
      )}

      {!loading && !error && documentation && (
        <div className="strategy-doc-content">
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
                    borderLeft: '4px solid #1890ff',
                    paddingLeft: 16,
                    marginLeft: 0,
                    marginBottom: 16,
                    color: '#595959',
                    fontStyle: 'italic',
                  }}
                  {...props}
                />
              ),
            }}
          >
            {documentation.content}
          </ReactMarkdown>
        </div>
      )}
    </Modal>
  );
}
