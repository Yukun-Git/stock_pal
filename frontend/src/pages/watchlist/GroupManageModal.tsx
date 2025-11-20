import { useState } from 'react';
import { Modal, List, Button, Input, ColorPicker, Space, Popconfirm, Form } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { WatchlistGroup } from '@/types';
import { useWatchlistStore } from '@/stores/useWatchlistStore';

interface Props {
  visible: boolean;
  onClose: () => void;
}

const PRESET_COLORS = [
  '#1890ff', // blue
  '#52c41a', // green
  '#faad14', // orange
  '#f5222d', // red
  '#722ed1', // purple
  '#13c2c2', // cyan
  '#eb2f96', // magenta
  '#999999', // gray
];

export default function GroupManageModal({ visible, onClose }: Props) {
  const { groups, createGroup, updateGroup, deleteGroup } = useWatchlistStore();
  const [form] = Form.useForm();
  const [editingGroup, setEditingGroup] = useState<WatchlistGroup | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedColor, setSelectedColor] = useState(PRESET_COLORS[0]);

  // Handle create
  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      await createGroup({
        name: values.name,
        color: selectedColor,
      });

      form.resetFields();
      setIsCreating(false);
      setSelectedColor(PRESET_COLORS[0]);
    } catch (error: any) {
      if (!error.errorFields) {
        // API error already handled in store
      }
    } finally {
      setLoading(false);
    }
  };

  // Handle edit
  const handleEdit = (group: WatchlistGroup) => {
    setEditingGroup(group);
    setSelectedColor(group.color || PRESET_COLORS[0]);
    form.setFieldsValue({
      name: group.name,
    });
  };

  const handleUpdate = async () => {
    if (!editingGroup) return;

    try {
      const values = await form.validateFields();
      setLoading(true);

      await updateGroup(editingGroup.id, {
        name: values.name,
        color: selectedColor,
      });

      form.resetFields();
      setEditingGroup(null);
      setSelectedColor(PRESET_COLORS[0]);
    } catch (error: any) {
      if (!error.errorFields) {
        // API error already handled in store
      }
    } finally {
      setLoading(false);
    }
  };

  // Handle delete
  const handleDelete = async (groupId: number) => {
    await deleteGroup(groupId);
  };

  // Handle cancel
  const handleCancel = () => {
    if (isCreating || editingGroup) {
      setIsCreating(false);
      setEditingGroup(null);
      form.resetFields();
      setSelectedColor(PRESET_COLORS[0]);
    } else {
      onClose();
    }
  };

  const sortedGroups = [...groups].sort((a, b) => a.sort_order - b.sort_order);

  return (
    <Modal
      title="管理分组"
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={600}
    >
      {/* Create/Edit Form */}
      {(isCreating || editingGroup) && (
        <div style={{ marginBottom: '24px', padding: '16px', background: '#f5f5f5', borderRadius: '4px' }}>
          <Form form={form} layout="vertical">
            <Form.Item
              name="name"
              label="分组名称"
              rules={[
                { required: true, message: '请输入分组名称' },
                { max: 50, message: '分组名称最多50个字符' },
              ]}
            >
              <Input placeholder="输入分组名称" />
            </Form.Item>

            <Form.Item label="分组颜色">
              <Space wrap>
                {PRESET_COLORS.map((color) => (
                  <div
                    key={color}
                    onClick={() => setSelectedColor(color)}
                    style={{
                      width: '32px',
                      height: '32px',
                      backgroundColor: color,
                      borderRadius: '4px',
                      cursor: 'pointer',
                      border: selectedColor === color ? '3px solid #000' : '1px solid #d9d9d9',
                    }}
                  />
                ))}
                <ColorPicker
                  value={selectedColor}
                  onChange={(color) => setSelectedColor(color.toHexString())}
                />
              </Space>
            </Form.Item>
          </Form>

          <Space>
            <Button type="primary" onClick={editingGroup ? handleUpdate : handleCreate} loading={loading}>
              {editingGroup ? '保存' : '创建'}
            </Button>
            <Button onClick={handleCancel}>取消</Button>
          </Space>
        </div>
      )}

      {/* Create Button */}
      {!isCreating && !editingGroup && (
        <Button
          type="dashed"
          icon={<PlusOutlined />}
          onClick={() => setIsCreating(true)}
          block
          style={{ marginBottom: '16px' }}
        >
          新建分组
        </Button>
      )}

      {/* Group List */}
      <List
        dataSource={sortedGroups}
        locale={{ emptyText: '暂无分组' }}
        renderItem={(group) => (
          <List.Item
            actions={[
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleEdit(group)}
              >
                编辑
              </Button>,
              group.is_default ? (
                <Button type="link" size="small" disabled>
                  不可删除
                </Button>
              ) : (
                <Popconfirm
                  title="确定删除这个分组吗?"
                  description='分组内的股票将移至"未分类"'
                  onConfirm={() => handleDelete(group.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>
              ),
            ]}
          >
            <List.Item.Meta
              avatar={
                <div
                  style={{
                    width: '40px',
                    height: '40px',
                    backgroundColor: group.color || '#999',
                    borderRadius: '4px',
                  }}
                />
              }
              title={
                <div>
                  {group.name}
                  {group.is_default && (
                    <span style={{ marginLeft: '8px', fontSize: '12px', color: '#999' }}>
                      (默认)
                    </span>
                  )}
                </div>
              }
              description={`包含 ${group.stock_count || 0} 只股票`}
            />
          </List.Item>
        )}
      />
    </Modal>
  );
}
