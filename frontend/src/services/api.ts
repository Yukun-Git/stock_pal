import axios from 'axios';
import type {
  Stock,
  Strategy,
  StrategyDocumentation,
  BacktestRequest,
  BacktestResponse,
} from '@/types';

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
};

export default api;
