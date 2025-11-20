import React from 'react';
import { Tag, Tooltip } from 'antd';
import { ApiOutlined, CheckCircleOutlined } from '@ant-design/icons';

interface DataSourceIndicatorProps {
  dataSource?: string;
  size?: 'small' | 'default';
  showIcon?: boolean;
}

/**
 * 数据源指示器组件
 * 显示当前使用的数据源
 */
const DataSourceIndicator: React.FC<DataSourceIndicatorProps> = ({
  dataSource,
  size = 'default',
  showIcon = true,
}) => {
  if (!dataSource) {
    return null;
  }

  // 数据源显示名称映射
  const displayNames: Record<string, string> = {
    'akshare': 'AkShare',
    'yfinance': 'Yahoo Finance',
    'baostock': '证券宝',
  };

  // 数据源颜色映射
  const colors: Record<string, string> = {
    'akshare': 'blue',
    'yfinance': 'purple',
    'baostock': 'green',
  };

  const displayName = displayNames[dataSource] || dataSource;
  const color = colors[dataSource] || 'default';

  return (
    <Tooltip title={`数据来源: ${displayName}`}>
      <Tag
        icon={showIcon ? <ApiOutlined /> : <CheckCircleOutlined />}
        color={color}
        style={{ fontSize: size === 'small' ? 12 : 14 }}
      >
        {displayName}
      </Tag>
    </Tooltip>
  );
};

export default DataSourceIndicator;
