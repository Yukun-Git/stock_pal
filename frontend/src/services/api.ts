import axios from 'axios';
import type {
  Stock,
  Strategy,
  StrategyDocumentation,
  BacktestRequest,
  BacktestResponse,
  BenchmarkOption,
  DataAdapter,
  AdapterStatus,
  AdapterMetrics,
  HealthCheckResponse,
} from '@/types';
import { getAuthToken, clearAuth } from '@/utils/auth';

// Use relative path to leverage Vite proxy in development
// In production, this will be replaced by nginx proxy
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for backtest operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);

    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
      // Clear auth data
      clearAuth();

      // Redirect to login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export const stockApi = {
  /**
   * Search stocks by keyword
   */
  searchStocks: async (keyword: string): Promise<Stock[]> => {
    const response = await api.get('/api/v1/stocks/search', {
      params: { keyword },
    });
    return response.data.data;
  },

  /**
   * Get stock list
   */
  getStockList: async (): Promise<Stock[]> => {
    const response = await api.get('/api/v1/stocks');
    return response.data.data;
  },

  /**
   * Get stock data
   */
  getStockData: async (
    symbol: string,
    startDate?: string,
    endDate?: string,
    includeIndicators = false
  ) => {
    const response = await api.get(`/api/v1/stocks/${symbol}/data`, {
      params: {
        start_date: startDate,
        end_date: endDate,
        include_indicators: includeIndicators,
      },
    });
    return response.data.data;
  },
};

export const strategyApi = {
  /**
   * Get all available strategies
   */
  getStrategies: async (): Promise<Strategy[]> => {
    const response = await api.get('/api/v1/strategies');
    return response.data.data;
  },

  /**
   * Get strategy documentation
   */
  getStrategyDocumentation: async (strategyId: string): Promise<StrategyDocumentation> => {
    const response = await api.get(`/api/v1/strategies/${strategyId}/documentation`);
    return response.data.data;
  },
};

export const backtestApi = {
  /**
   * Run backtest
   */
  runBacktest: async (request: BacktestRequest): Promise<BacktestResponse> => {
    const response = await api.post('/api/v1/backtest', request);

    console.log('Raw response.data type:', typeof response.data);
    console.log('Raw response.data:', response.data);

    // Handle both string and object responses
    let data = response.data;
    if (typeof data === 'string') {
      console.log('Response is string, parsing JSON...');
      try {
        // Replace Infinity with null to make it valid JSON
        const cleanedData = data.replace(/:\s*Infinity/g, ': null')
                                .replace(/:\s*-Infinity/g, ': null')
                                .replace(/:\s*NaN/g, ': null');
        data = JSON.parse(cleanedData);
        console.log('JSON parse successful');
      } catch (error) {
        console.error('JSON parse failed:', error);
        console.log('String content:', data.substring(0, 200));
        throw error;
      }
    }

    console.log('Parsed data:', data);
    console.log('data.success:', data.success);
    console.log('data.data exists:', !!data.data);

    if (!data.data) {
      console.error('data.data is missing! Full data:', data);
      throw new Error('Invalid API response: data.data is missing');
    }

    return data.data;
  },

  /**
   * Get available benchmark indices
   */
  getBenchmarks: async (): Promise<BenchmarkOption[]> => {
    const response = await api.get('/api/v1/benchmarks');
    return response.data.data;
  },
};

// Watchlist API
export const watchlistApi = {
  /**
   * Get user's watchlist
   */
  getWatchlist: async (params?: {
    group_id?: number;
    sort_by?: 'code' | 'name' | 'created_at';
    sort_order?: 'asc' | 'desc';
    include_quotes?: boolean;
  }) => {
    const response = await api.get('/api/v1/watchlist', { params });
    return response.data.data;
  },

  /**
   * Add stock to watchlist
   */
  addStock: async (data: import('@/types').AddWatchlistStockRequest) => {
    const response = await api.post('/api/v1/watchlist', data);
    return response.data.data;
  },

  /**
   * Update watchlist item
   */
  updateStock: async (stockId: number, data: import('@/types').UpdateWatchlistStockRequest) => {
    const response = await api.put(`/api/v1/watchlist/${stockId}`, data);
    return response.data.data;
  },

  /**
   * Delete watchlist item
   */
  deleteStock: async (stockId: number) => {
    const response = await api.delete(`/api/v1/watchlist/${stockId}`);
    return response.data;
  },

  /**
   * Batch delete watchlist items
   */
  batchDelete: async (data: import('@/types').BatchDeleteWatchlistRequest) => {
    const response = await api.delete('/api/v1/watchlist/batch', { data });
    return response.data.data;
  },

  /**
   * Batch import watchlist items
   */
  batchImport: async (data: import('@/types').BatchImportWatchlistRequest) => {
    const response = await api.post('/api/v1/watchlist/batch', data);
    return response.data.data as import('@/types').BatchImportWatchlistResponse;
  },

  /**
   * Check if stock is in watchlist
   */
  checkStock: async (stockCode: string) => {
    const response = await api.get(`/api/v1/watchlist/check/${stockCode}`);
    return response.data.data as import('@/types').CheckWatchlistResponse;
  },
};

// Watchlist Groups API
export const watchlistGroupApi = {
  /**
   * Get user's groups
   */
  getGroups: async (params?: { include_counts?: boolean }) => {
    const response = await api.get('/api/v1/watchlist/groups', { params });
    return response.data.data;
  },

  /**
   * Create a new group
   */
  createGroup: async (data: import('@/types').CreateGroupRequest) => {
    const response = await api.post('/api/v1/watchlist/groups', data);
    return response.data.data;
  },

  /**
   * Update a group
   */
  updateGroup: async (groupId: number, data: import('@/types').UpdateGroupRequest) => {
    const response = await api.put(`/api/v1/watchlist/groups/${groupId}`, data);
    return response.data.data;
  },

  /**
   * Delete a group
   */
  deleteGroup: async (groupId: number) => {
    const response = await api.delete(`/api/v1/watchlist/groups/${groupId}`);
    return response.data;
  },
};

// Data Source Adapter API
export const adapterApi = {
  /**
   * Get all registered adapters
   */
  getAdapters: async (): Promise<DataAdapter[]> => {
    const response = await api.get('/api/v1/adapters');
    return response.data.data;
  },

  /**
   * Get adapter status (metadata + health + metrics)
   */
  getAdapterStatus: async (): Promise<AdapterStatus[]> => {
    const response = await api.get('/api/v1/adapters/status');
    return response.data.data;
  },

  /**
   * Run health check on all adapters
   */
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await api.get('/api/v1/adapters/health');
    return response.data.data;
  },

  /**
   * Get metrics for all adapters or a specific adapter
   */
  getMetrics: async (adapterName?: string): Promise<Record<string, AdapterMetrics> | AdapterMetrics> => {
    const url = adapterName
      ? `/api/v1/adapters/metrics/${adapterName}`
      : '/api/v1/adapters/metrics';
    const response = await api.get(url);
    return response.data.data;
  },
};

// AI Analysis API
export const aiApi = {
  /**
   * Analyze backtest results using AI
   */
  analyzeBacktest: async (data: {
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
  }) => {
    const response = await api.post('/api/v1/backtest/analyze', data);
    return response.data.data;
  },
};

export default api;
