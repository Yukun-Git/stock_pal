import { RiseOutlined, FallOutlined, MinusOutlined } from '@ant-design/icons';
import type { ReactNode } from 'react';

export interface StatusConfig {
  color: string;
  icon: ReactNode;
  label: string;
}

export interface ProximityConfig {
  badge: {
    text: string;
    emoji?: string;
    bgColor: string;
    textColor: string;
    fontWeight?: string;
  };
}

/**
 * Status Configuration Map
 *
 * Maps analysis status to corresponding colors, icons, and labels.
 * This eliminates hardcoded if-else chains for status rendering.
 *
 * Before refactoring:
 * if (analysis.status === 'bullish' || analysis.status.includes('buy')) {
 *   statusColor = '#ff4d4f';
 *   statusIcon = <RiseOutlined />;
 * }
 *
 * After refactoring:
 * const config = getStatusConfig(analysis.status);
 * // config.color, config.icon automatically determined
 */
export const STATUS_CONFIG: Record<string, StatusConfig> = {
  bullish: {
    color: '#ff4d4f',
    icon: <RiseOutlined />,
    label: '看涨',
  },
  bearish: {
    color: '#52c41a',
    icon: <FallOutlined />,
    label: '看跌',
  },
  neutral: {
    color: '#8c8c8c',
    icon: <MinusOutlined />,
    label: '中性',
  },
  // Additional status types can be added here without modifying component code
  overbought: {
    color: '#fa8c16',
    icon: <RiseOutlined />,
    label: '超买',
  },
  oversold: {
    color: '#52c41a',
    icon: <FallOutlined />,
    label: '超卖',
  },
};

/**
 * Proximity Configuration Map
 *
 * Maps proximity levels to badge styling.
 * Supports easy addition of new proximity levels.
 */
export const PROXIMITY_CONFIG: Record<string, ProximityConfig> = {
  very_close: {
    badge: {
      text: '非常接近',
      emoji: '⚠️',
      bgColor: '#fff2e8',
      textColor: '#fa8c16',
      fontWeight: 'bold',
    },
  },
  close: {
    badge: {
      text: '接近',
      bgColor: '#e6f7ff',
      textColor: '#1890ff',
    },
  },
  far: {
    badge: {
      text: '较远',
      bgColor: '#f0f0f0',
      textColor: '#8c8c8c',
    },
  },
  // Additional proximity levels can be added here
};

/**
 * Get status configuration with fallback logic
 *
 * Supports both exact matching and fuzzy matching for flexibility.
 *
 * @param status - Status string from backend
 * @returns StatusConfig object with color, icon, and label
 */
export function getStatusConfig(status: string): StatusConfig {
  // Normalize status to lowercase for case-insensitive matching
  const normalizedStatus = status.toLowerCase();

  // Try exact match first
  if (STATUS_CONFIG[normalizedStatus]) {
    return STATUS_CONFIG[normalizedStatus];
  }

  // Fuzzy matching for compatibility with various status strings
  if (normalizedStatus.includes('buy') || normalizedStatus.includes('bullish')) {
    return STATUS_CONFIG.bullish;
  }
  if (normalizedStatus.includes('sell') || normalizedStatus.includes('bearish')) {
    return STATUS_CONFIG.bearish;
  }
  if (normalizedStatus.includes('overbought')) {
    return STATUS_CONFIG.overbought;
  }
  if (normalizedStatus.includes('oversold')) {
    return STATUS_CONFIG.oversold;
  }

  // Default fallback
  return STATUS_CONFIG.neutral;
}

/**
 * Get proximity configuration
 *
 * @param proximity - Proximity level from backend
 * @returns ProximityConfig object or null if not found
 */
export function getProximityConfig(proximity?: string): ProximityConfig | null {
  if (!proximity || !PROXIMITY_CONFIG[proximity]) {
    return null;
  }
  return PROXIMITY_CONFIG[proximity];
}
