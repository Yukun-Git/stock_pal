import { Tag } from 'antd';
import { useWatchlistStore } from '@/stores/useWatchlistStore';

export default function GroupFilter() {
  const { groups, selectedGroupId, setSelectedGroup, stocks } = useWatchlistStore();

  // Calculate stock count for "All" group
  const allStocksCount = stocks.length;

  // Calculate stock count for "Uncategorized" group (group_id = null)
  const uncategorizedCount = stocks.filter((stock) => stock.group_id === null).length;

  const handleGroupClick = (groupId: number | null) => {
    setSelectedGroup(groupId);
  };

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
      {/* All */}
      <Tag.CheckableTag
        checked={selectedGroupId === null}
        onChange={() => handleGroupClick(null)}
        style={{
          padding: '4px 12px',
          fontSize: '14px',
          cursor: 'pointer',
          border: '1px solid #d9d9d9',
          borderRadius: '4px',
        }}
      >
        全部 ({allStocksCount})
      </Tag.CheckableTag>

      {/* Uncategorized */}
      {uncategorizedCount > 0 && (
        <Tag.CheckableTag
          checked={selectedGroupId === 0}
          onChange={() => handleGroupClick(0)}
          style={{
            padding: '4px 12px',
            fontSize: '14px',
            cursor: 'pointer',
            border: '1px solid #d9d9d9',
            borderRadius: '4px',
          }}
        >
          未分类 ({uncategorizedCount})
        </Tag.CheckableTag>
      )}

      {/* Custom Groups */}
      {groups
        .sort((a, b) => a.sort_order - b.sort_order)
        .map((group) => (
          <Tag.CheckableTag
            key={group.id}
            checked={selectedGroupId === group.id}
            onChange={() => handleGroupClick(group.id)}
            style={{
              padding: '4px 12px',
              fontSize: '14px',
              cursor: 'pointer',
              border: '1px solid #d9d9d9',
              borderRadius: '4px',
              backgroundColor: group.color || undefined,
              color: group.color ? '#fff' : undefined,
            }}
          >
            {group.name} ({group.stock_count || 0})
          </Tag.CheckableTag>
        ))}
    </div>
  );
}
