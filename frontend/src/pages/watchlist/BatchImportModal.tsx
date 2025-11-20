import { useState } from 'react';
import { Modal, Input, Select, Alert, Form, message } from 'antd';
import { useWatchlistStore } from '@/stores/useWatchlistStore';
import type { BatchImportWatchlistResponse } from '@/types';

interface Props {
  visible: boolean;
  onClose: () => void;
}

export default function BatchImportModal({ visible, onClose }: Props) {
  const { groups, batchImportStocks } = useWatchlistStore();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BatchImportWatchlistResponse | null>(null);

  // Parse stock codes from text
  const parseStockCodes = (text: string): Array<{ stock_code: string; stock_name: string }> => {
    const lines = text.trim().split('\n');
    const stocks: Array<{ stock_code: string; stock_name: string }> = [];

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      // Support formats:
      // 1. "600000" or "03690.HK" (code only, name will be filled with code)
      // 2. "600000 浦发银行" or "03690.HK 美团" (code and name separated by space/tab)
      // 3. "600000,浦发银行" or "03690.HK,美团" (code and name separated by comma)
      // 4. "600000\t浦发银行" or "03690.HK\t美团" (code and name separated by tab)

      const parts = trimmed.split(/[\s,\t]+/);
      const code = parts[0].trim();

      // Validate stock code format (A-share: 6 digits, or HK stock: 5 digits + .HK)
      if (!/^(\d{6}(\.(SH|SZ))?|\d{5}\.HK)$/.test(code)) {
        continue;
      }

      const name = parts[1]?.trim() || code;

      stocks.push({
        stock_code: code,
        stock_name: name,
      });
    }

    return stocks;
  };

  // Handle submit
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const stocksText = values.stocks_text;

      if (!stocksText || !stocksText.trim()) {
        message.error('请输入股票代码');
        return;
      }

      const stocks = parseStockCodes(stocksText);

      if (stocks.length === 0) {
        message.error('未识别到有效的股票代码');
        return;
      }

      if (stocks.length > 100) {
        message.error('单次最多导入100只股票');
        return;
      }

      setLoading(true);

      try {
        const importResult = await batchImportStocks({
          stocks,
          group_id: values.group_id,
          skip_duplicates: true,
        });

          setResult(importResult);

        // If all succeeded, close modal
        if (importResult.failed.length === 0) {
          setTimeout(() => {
            handleClose();
          }, 1500);
        }
      } catch (error) {
        // Error already handled in store
      } finally {
        setLoading(false);
      }
    } catch (error) {
      // Validation error
      return;
    }
  };

  // Handle close
  const handleClose = () => {
    form.resetFields();
    setResult(null);
    onClose();
  };

  return (
    <Modal
      title="批量导入自选股"
      open={visible}
      onOk={handleSubmit}
      onCancel={handleClose}
      okText="导入"
      cancelText="取消"
      confirmLoading={loading}
      width={600}
    >
      <Form form={form} layout="vertical" style={{ marginTop: '24px' }}>
        <Alert
          message="导入说明"
          description={
            <div>
              <p>支持以下格式（每行一只股票）：</p>
              <ul style={{ marginBottom: 0, paddingLeft: '20px' }}>
                <li>仅代码：600000</li>
                <li>代码和名称（空格分隔）：600000 浦发银行</li>
                <li>代码和名称（逗号分隔）：600000,浦发银行</li>
              </ul>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: '16px' }}
        />

        <Form.Item
          name="stocks_text"
          label="股票列表"
          rules={[{ required: true, message: '请输入股票代码' }]}
        >
          <Input.TextArea
            rows={10}
            placeholder={`输入股票代码，每行一只股票，例如：\n600000 浦发银行\n000001 平安银行\n600036 招商银行`}
          />
        </Form.Item>

        <Form.Item name="group_id" label="导入到分组">
          <Select
            placeholder="选择分组（可选）"
            allowClear
            options={[
              { label: '未分类', value: null },
              ...groups.map((group) => ({
                label: group.name,
                value: group.id,
              })),
            ]}
          />
        </Form.Item>
      </Form>

      {/* Result */}
      {result && (
        <Alert
          message={
            result.failed.length === 0
              ? '导入成功'
              : `导入完成（部分失败）`
          }
          description={
            <div>
              <p>成功导入: {result.imported_count} 只</p>
              {result.skipped_count > 0 && <p>跳过（已存在）: {result.skipped_count} 只</p>}
              {result.failed.length > 0 && (
                <div>
                  <p>失败: {result.failed.length} 只</p>
                  <div style={{ maxHeight: '150px', overflow: 'auto' }}>
                    {result.failed.map((fail, index) => (
                      <div key={index} style={{ fontSize: '12px', color: '#999' }}>
                        {fail.stock_code || fail.stock?.stock_code} - {fail.reason}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          }
          type={result.failed.length === 0 ? 'success' : 'warning'}
          showIcon
          style={{ marginTop: '16px' }}
        />
      )}
    </Modal>
  );
}
