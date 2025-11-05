import axios from 'axios';
import type {
  Stock,
  Strategy,
  BacktestRequest,
  BacktestResponse,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL !== undefined
  ? import.meta.env.VITE_API_BASE_URL
  : 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for backtest operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
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
};

export const backtestApi = {
  /**
   * Run backtest
   */
  runBacktest: async (request: BacktestRequest): Promise<BacktestResponse> => {
    const response = await api.post('/api/v1/backtest', request);
    return response.data.data;
  },
};

export default api;
