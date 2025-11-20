import { useState } from 'react';
import { Modal, Select, Input, Form, message } from 'antd';
import { stockApi } from '@/services/api';
import { useWatchlistStore } from '@/stores/useWatchlistStore';
import type { Stock } from '@/types';

interface Props {
  visible: boolean;
  onClose: () => void;
  defaultStock?: Stock;
}

export default function AddStockModal({ visible, onClose, defaultStock }: Props) {
  const { groups, addStock } = useWatchlistStore();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [stockOptions, setStockOptions] = useState<Stock[]>([]);

  // Handle stock search
  const handleSearch = async (keyword: string) => {
    if (!keyword || keyword.length < 2) {
      setStockOptions([]);
      return;
    }

    try {
      setSearching(true);
      const results = await stockApi.searchStocks(keyword);
      setStockOptions(results);
    } catch (error) {
      console.error('搜索失败:', error);
      message.error('搜索失败');
    } finally {
      setSearching(false);
    }
  };

  // Handle stock selection
  const handleStockSelect = (value: string) => {
    // The value is in format "code|name"
    const [code, name] = value.split('|');
    form.setFieldsValue({
      stock_code: code,
      stock_name: name,
    });
  };

  // Handle form submission
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      await addStock({
        stock_code: values.stock_code,
        stock_name: values.stock_name,
        group_id: values.group_id,
        note: values.note,
      });

      form.resetFields();
      setStockOptions([]);
      onClose();
    } catch (error: any) {
      // Validation errors or API errors
      if (error.errorFields) {
        // Form validation error
        return;
      }
      // API error already handled in store
    } finally {
      setLoading(false);
    }
  };

  // Handle modal cancel
  const handleCancel = () => {
    form.resetFields();
    setStockOptions([]);
    onClose();
  };

  // Initialize form with default stock if provided
  if (defaultStock && visible) {
    form.setFieldsValue({
      stock_code: defaultStock.code,
      stock_name: defaultStock.name,
    });
  }

  return (
    <Modal
      title="添加自选股"
      open={visible}
      onOk={handleSubmit}
      onCancel={handleCancel}
      okText="添加"
      cancelText="取消"
      confirmLoading={loading}
      destroyOnClose
    >
      <Form form={form} layout="vertical" style={{ marginTop: '24px' }}>
        <Form.Item label="搜索股票" required>
          <Select
            showSearch
            placeholder="输入股票代码或名称"
            filterOption={false}
            onSearch={handleSearch}
            onChange={handleStockSelect}
            loading={searching}
            notFoundContent={searching ? '搜索中...' : '未找到股票'}
            options={stockOptions.map((stock) => ({
              label: `${stock.code} ${stock.name}`,
              value: `${stock.code}|${stock.name}`,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="stock_code"
          label="股票代码"
          rules={[
            { required: true, message: '请输入股票代码' },
            {
              pattern: /^(\d{6}(\.(SH|SZ))?|\d{5}\.HK)$/,
              message: '股票代码格式不正确（A股6位数字或港股5位数字.HK）'
            },
          ]}
          hidden
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="stock_name"
          label="股票名称"
          rules={[{ required: true, message: '请输入股票名称' }]}
          hidden
        >
          <Input />
        </Form.Item>

        <Form.Item name="group_id" label="分组">
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

        <Form.Item name="note" label="备注">
          <Input.TextArea
            rows={3}
            placeholder="添加备注（可选）"
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
