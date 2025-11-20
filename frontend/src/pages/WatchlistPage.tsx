import { useEffect, useState } from 'react';
import { Card, Space, Input, Button, Empty } from 'antd';
import { PlusOutlined, ReloadOutlined, UploadOutlined, SettingOutlined } from '@ant-design/icons';
import { useWatchlistStore } from '@/stores/useWatchlistStore';
import GroupFilter from './watchlist/GroupFilter';
import WatchlistTable from './watchlist/WatchlistTable';
import AddStockModal from './watchlist/AddStockModal';
import GroupManageModal from './watchlist/GroupManageModal';
import BatchImportModal from './watchlist/BatchImportModal';

const { Search } = Input;

export default function WatchlistPage() {
  const {
    isLoading,
    stocks,
    fetchWatchlist,
    fetchGroups,
    setSearchKeyword,
    getFilteredStocks,
  } = useWatchlistStore();

  const [isAddModalVisible, setIsAddModalVisible] = useState(false);
  const [isGroupManageVisible, setIsGroupManageVisible] = useState(false);
  const [isImportModalVisible, setIsImportModalVisible] = useState(false);

  // Load data on mount
  useEffect(() => {
    fetchWatchlist();
    fetchGroups();
  }, [fetchWatchlist, fetchGroups]);

  const filteredStocks = getFilteredStocks();
  const isEmpty = stocks.length === 0;

  const handleSearch = (value: string) => {
    setSearchKeyword(value);
  };

  const handleRefresh = () => {
    fetchWatchlist();
    fetchGroups();
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '20px', fontWeight: 'bold' }}>我的自选股</span>
            <Space>
              <Search
                placeholder="搜索股票代码、名称或备注"
                allowClear
                style={{ width: 300 }}
                onSearch={handleSearch}
                onChange={(e) => handleSearch(e.target.value)}
              />
              <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
                刷新
              </Button>
              <Button icon={<UploadOutlined />} onClick={() => setIsImportModalVisible(true)}>
                批量导入
              </Button>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setIsAddModalVisible(true)}
              >
                添加自选股
              </Button>
              <Button
                icon={<SettingOutlined />}
                onClick={() => setIsGroupManageVisible(true)}
              >
                管理分组
              </Button>
            </Space>
          </div>
        }
        loading={isLoading}
        bodyStyle={{ padding: 0 }}
      >
        {/* Group Filter */}
        <div style={{ padding: '16px 24px 0' }}>
          <GroupFilter />
        </div>

        {/* Main Content */}
        <div style={{ padding: '16px 0' }}>
          {isEmpty ? (
            // Empty State
            <div style={{ padding: '60px 24px', textAlign: 'center' }}>
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <div>
                    <div style={{ fontSize: '16px', marginBottom: '8px' }}>
                      还没有添加自选股
                    </div>
                    <div style={{ color: '#888', marginBottom: '24px' }}>
                      添加你关注的股票，开始量化投资之旅！
                    </div>
                  </div>
                }
              >
                <Button
                  type="primary"
                  size="large"
                  icon={<PlusOutlined />}
                  onClick={() => setIsAddModalVisible(true)}
                >
                  添加第一只自选股
                </Button>
              </Empty>
            </div>
          ) : filteredStocks.length === 0 ? (
            // No Results
            <div style={{ padding: '60px 24px', textAlign: 'center' }}>
              <Empty description="没有找到匹配的股票" />
            </div>
          ) : (
            // Watchlist Table
            <WatchlistTable stocks={filteredStocks} />
          )}
        </div>
      </Card>

      {/* Modals */}
      <AddStockModal
        visible={isAddModalVisible}
        onClose={() => setIsAddModalVisible(false)}
      />

      <GroupManageModal
        visible={isGroupManageVisible}
        onClose={() => setIsGroupManageVisible(false)}
      />

      <BatchImportModal
        visible={isImportModalVisible}
        onClose={() => setIsImportModalVisible(false)}
      />
    </div>
  );
}
