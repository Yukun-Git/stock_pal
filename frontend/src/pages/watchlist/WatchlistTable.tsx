import { useState } from 'react';
import { Table, Tag, Button, Space, Popconfirm, Modal, Input, Select, Tooltip } from 'antd';
import {
  DeleteOutlined,
  EditOutlined,
  LineChartOutlined,
  DeleteFilled,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import type { WatchlistStock } from '@/types';
import { useWatchlistStore } from '@/stores/useWatchlistStore';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

interface Props {
  stocks: WatchlistStock[];
}

export default function WatchlistTable({ stocks }: Props) {
  const navigate = useNavigate();
  const {
    groups,
    selectedStockIds,
    toggleStockSelection,
    clearSelection,
    deleteStock,
    updateStock,
    batchDeleteStocks,
  } = useWatchlistStore();

  const [editingStock, setEditingStock] = useState<WatchlistStock | null>(null);
  const [editGroupId, setEditGroupId] = useState<number | null>(null);
  const [editNote, setEditNote] = useState('');

  const hasSelection = selectedStockIds.size > 0;

  // Handle row selection
  const rowSelection = {
    selectedRowKeys: Array.from(selectedStockIds),
    onChange: (selectedRowKeys: React.Key[]) => {
      clearSelection();
      selectedRowKeys.forEach((key) => toggleStockSelection(key as number));
    },
  };

  // Handle delete
  const handleDelete = async (id: number) => {
    await deleteStock(id);
  };

  // Handle batch delete
  const handleBatchDelete = async () => {
    await batchDeleteStocks(Array.from(selectedStockIds));
  };

  // Handle edit
  const handleEdit = (stock: WatchlistStock) => {
    setEditingStock(stock);
    setEditGroupId(stock.group_id || null);
    setEditNote(stock.note || '');
  };

  const handleEditConfirm = async () => {
    if (!editingStock) return;

    await updateStock(editingStock.id, {
      group_id: editGroupId || undefined,
      note: editNote || undefined,
    });

    setEditingStock(null);
  };

  // Handle backtest navigation
  const handleBacktest = (stockCode: string) => {
    navigate(`/backtest?symbol=${stockCode}`);
  };

  const columns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
      render: (code: string) => (
        <span style={{ fontFamily: 'monospace', fontWeight: 500 }}>{code}</span>
      ),
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 150,
    },
    {
      title: '分组',
      dataIndex: 'group_name',
      key: 'group_name',
      width: 120,
      render: (groupName: string | undefined, record: WatchlistStock) => {
        if (!groupName && !record.group_id) {
          return <Tag color="default">未分类</Tag>;
        }
        const group = groups.find((g) => g.id === record.group_id);
        return (
          <Tag color={group?.color || 'blue'}>
            {groupName || '未分类'}
          </Tag>
        );
      },
    },
    {
      title: '备注',
      dataIndex: 'note',
      key: 'note',
      width: 200,
      ellipsis: {
        showTitle: false,
      },
      render: (note: string | undefined) => (
        <Tooltip placement="topLeft" title={note}>
          {note || '-'}
        </Tooltip>
      ),
    },
    {
      title: '添加时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (createdAt: string) => (
        <Tooltip title={dayjs(createdAt).format('YYYY-MM-DD HH:mm:ss')}>
          {dayjs(createdAt).fromNow()}
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: WatchlistStock) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<LineChartOutlined />}
            onClick={() => handleBacktest(record.stock_code)}
          >
            回测
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除这只股票吗?"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Batch Action Bar */}
      {hasSelection && (
        <div
          style={{
            padding: '12px 24px',
            background: '#e6f7ff',
            borderBottom: '1px solid #91d5ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span>
            已选择 <strong>{selectedStockIds.size}</strong> 只股票
          </span>
          <Space>
            <Button size="small" onClick={clearSelection}>
              取消选择
            </Button>
            <Popconfirm
              title={`确定删除选中的 ${selectedStockIds.size} 只股票吗?`}
              onConfirm={handleBatchDelete}
              okText="确定"
              cancelText="取消"
            >
              <Button size="small" danger icon={<DeleteFilled />}>
                批量删除
              </Button>
            </Popconfirm>
          </Space>
        </div>
      )}

      {/* Table */}
      <Table
        rowSelection={rowSelection}
        columns={columns}
        dataSource={stocks}
        rowKey="id"
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 只股票`,
        }}
        scroll={{ x: 1000 }}
      />

      {/* Edit Modal */}
      <Modal
        title="编辑自选股"
        open={!!editingStock}
        onOk={handleEditConfirm}
        onCancel={() => setEditingStock(null)}
        okText="保存"
        cancelText="取消"
      >
        {editingStock && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <div style={{ marginBottom: '8px' }}>
                股票信息: {editingStock.stock_code} {editingStock.stock_name}
              </div>
            </div>

            <div>
              <div style={{ marginBottom: '8px' }}>分组</div>
              <Select
                style={{ width: '100%' }}
                placeholder="选择分组"
                value={editGroupId}
                onChange={setEditGroupId}
                allowClear
                options={[
                  { label: '未分类', value: null },
                  ...groups.map((group) => ({
                    label: group.name,
                    value: group.id,
                  })),
                ]}
              />
            </div>

            <div>
              <div style={{ marginBottom: '8px' }}>备注</div>
              <Input.TextArea
                rows={3}
                placeholder="添加备注..."
                value={editNote}
                onChange={(e) => setEditNote(e.target.value)}
                maxLength={500}
                showCount
              />
            </div>
          </Space>
        )}
      </Modal>
    </div>
  );
}
