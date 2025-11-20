import { create } from 'zustand';
import { message } from 'antd';
import type {
  WatchlistStock,
  WatchlistGroup,
  AddWatchlistStockRequest,
  UpdateWatchlistStockRequest,
  BatchImportWatchlistRequest,
  BatchImportWatchlistResponse,
  CreateGroupRequest,
  UpdateGroupRequest,
} from '@/types';
import { watchlistApi, watchlistGroupApi } from '@/services/api';

interface WatchlistState {
  // Data
  stocks: WatchlistStock[];
  groups: WatchlistGroup[];

  // UI State
  selectedGroupId: number | null; // null means "All"
  selectedStockIds: Set<number>;
  searchKeyword: string;
  sortBy: 'code' | 'name' | 'created_at';
  sortOrder: 'asc' | 'desc';

  // Loading State
  isLoading: boolean;
  isRefreshingQuotes: boolean;

  // Actions - Watchlist
  fetchWatchlist: () => Promise<void>;
  addStock: (data: AddWatchlistStockRequest) => Promise<void>;
  updateStock: (id: number, data: UpdateWatchlistStockRequest) => Promise<void>;
  deleteStock: (id: number) => Promise<void>;
  batchDeleteStocks: (ids: number[]) => Promise<void>;
  batchImportStocks: (data: BatchImportWatchlistRequest) => Promise<BatchImportWatchlistResponse>;

  // Actions - Groups
  fetchGroups: () => Promise<void>;
  createGroup: (data: CreateGroupRequest) => Promise<void>;
  updateGroup: (id: number, data: UpdateGroupRequest) => Promise<void>;
  deleteGroup: (id: number) => Promise<void>;

  // Actions - UI
  setSelectedGroup: (groupId: number | null) => void;
  toggleStockSelection: (id: number) => void;
  clearSelection: () => void;
  setSearchKeyword: (keyword: string) => void;
  setSorting: (sortBy: 'code' | 'name' | 'created_at', sortOrder?: 'asc' | 'desc') => void;

  // Computed
  getFilteredStocks: () => WatchlistStock[];
}

export const useWatchlistStore = create<WatchlistState>((set, get) => ({
  // Initial State
  stocks: [],
  groups: [],
  selectedGroupId: null,
  selectedStockIds: new Set(),
  searchKeyword: '',
  sortBy: 'created_at',
  sortOrder: 'desc',
  isLoading: false,
  isRefreshingQuotes: false,

  // Fetch watchlist
  fetchWatchlist: async () => {
    try {
      set({ isLoading: true });
      const response = await watchlistApi.getWatchlist({
        sort_by: get().sortBy,
        sort_order: get().sortOrder,
        include_quotes: false, // Phase 3: set to true
      });
      set({ stocks: response.stocks, isLoading: false });
    } catch (error: any) {
      console.error('Failed to fetch watchlist:', error);
      message.error(error.response?.data?.error || '获取自选股列表失败');
      set({ isLoading: false });
    }
  },

  // Add stock
  addStock: async (data: AddWatchlistStockRequest) => {
    try {
      const newStock = await watchlistApi.addStock(data);
      set((state) => ({
        stocks: [newStock, ...state.stocks],
      }));
      message.success('添加成功');
    } catch (error: any) {
      console.error('Failed to add stock:', error);
      const errorMsg = error.response?.data?.error || '添加失败';
      message.error(errorMsg);
      throw error;
    }
  },

  // Update stock
  updateStock: async (id: number, data: UpdateWatchlistStockRequest) => {
    try {
      const updatedStock = await watchlistApi.updateStock(id, data);
      set((state) => ({
        stocks: state.stocks.map((stock) => (stock.id === id ? updatedStock : stock)),
      }));
      message.success('更新成功');
    } catch (error: any) {
      console.error('Failed to update stock:', error);
      message.error(error.response?.data?.error || '更新失败');
      throw error;
    }
  },

  // Delete stock
  deleteStock: async (id: number) => {
    try {
      await watchlistApi.deleteStock(id);
      set((state) => ({
        stocks: state.stocks.filter((stock) => stock.id !== id),
        selectedStockIds: new Set(
          Array.from(state.selectedStockIds).filter((stockId) => stockId !== id)
        ),
      }));
      message.success('删除成功');
    } catch (error: any) {
      console.error('Failed to delete stock:', error);
      message.error(error.response?.data?.error || '删除失败');
      throw error;
    }
  },

  // Batch delete stocks
  batchDeleteStocks: async (ids: number[]) => {
    try {
      const result = await watchlistApi.batchDelete({ ids });
      set((state) => ({
        stocks: state.stocks.filter((stock) => !ids.includes(stock.id)),
        selectedStockIds: new Set(),
      }));
      message.success(`已删除 ${result.deleted_count} 只股票`);
    } catch (error: any) {
      console.error('Failed to batch delete stocks:', error);
      message.error(error.response?.data?.error || '批量删除失败');
      throw error;
    }
  },

  // Batch import stocks
  batchImportStocks: async (data: BatchImportWatchlistRequest): Promise<BatchImportWatchlistResponse> => {
    const result = await watchlistApi.batchImport(data);

    // Refresh the list after import
    await get().fetchWatchlist();

    // Show result
    if (result.failed.length === 0) {
      message.success(`成功导入 ${result.imported_count} 只股票`);
    } else {
      message.warning(
        `导入完成：成功 ${result.imported_count} 只，跳过 ${result.skipped_count} 只，失败 ${result.failed.length} 只`
      );
    }

    return result;
  },

  // Fetch groups
  fetchGroups: async () => {
    try {
      const response = await watchlistGroupApi.getGroups({ include_counts: true });
      set({ groups: response.groups });
    } catch (error: any) {
      console.error('Failed to fetch groups:', error);
      message.error(error.response?.data?.error || '获取分组失败');
    }
  },

  // Create group
  createGroup: async (data: CreateGroupRequest) => {
    try {
      const newGroup = await watchlistGroupApi.createGroup(data);
      set((state) => ({
        groups: [...state.groups, newGroup],
      }));
      message.success('分组创建成功');
    } catch (error: any) {
      console.error('Failed to create group:', error);
      message.error(error.response?.data?.error || '创建分组失败');
      throw error;
    }
  },

  // Update group
  updateGroup: async (id: number, data: UpdateGroupRequest) => {
    try {
      const updatedGroup = await watchlistGroupApi.updateGroup(id, data);
      set((state) => ({
        groups: state.groups.map((group) => (group.id === id ? updatedGroup : group)),
      }));
      message.success('分组更新成功');
    } catch (error: any) {
      console.error('Failed to update group:', error);
      message.error(error.response?.data?.error || '更新分组失败');
      throw error;
    }
  },

  // Delete group
  deleteGroup: async (id: number) => {
    try {
      await watchlistGroupApi.deleteGroup(id);
      set((state) => ({
        groups: state.groups.filter((group) => group.id !== id),
        selectedGroupId: state.selectedGroupId === id ? null : state.selectedGroupId,
      }));

      // Refresh watchlist to update group_id for affected stocks
      await get().fetchWatchlist();

      message.success('分组已删除');
    } catch (error: any) {
      console.error('Failed to delete group:', error);
      message.error(error.response?.data?.error || '删除分组失败');
      throw error;
    }
  },

  // Set selected group
  setSelectedGroup: (groupId: number | null) => {
    set({ selectedGroupId: groupId, selectedStockIds: new Set() });
  },

  // Toggle stock selection
  toggleStockSelection: (id: number) => {
    set((state) => {
      const newSelection = new Set(state.selectedStockIds);
      if (newSelection.has(id)) {
        newSelection.delete(id);
      } else {
        newSelection.add(id);
      }
      return { selectedStockIds: newSelection };
    });
  },

  // Clear selection
  clearSelection: () => {
    set({ selectedStockIds: new Set() });
  },

  // Set search keyword
  setSearchKeyword: (keyword: string) => {
    set({ searchKeyword: keyword });
  },

  // Set sorting
  setSorting: (sortBy: 'code' | 'name' | 'created_at', sortOrder?: 'asc' | 'desc') => {
    const currentSortBy = get().sortBy;
    const currentSortOrder = get().sortOrder;

    // Toggle sort order if clicking the same column
    const newSortOrder =
      sortOrder || (sortBy === currentSortBy && currentSortOrder === 'asc' ? 'desc' : 'asc');

    set({ sortBy, sortOrder: newSortOrder });
  },

  // Get filtered stocks (computed)
  getFilteredStocks: () => {
    const { stocks, selectedGroupId, searchKeyword, sortBy, sortOrder } = get();

    let filtered = stocks;

    // Filter by group
    if (selectedGroupId !== null) {
      filtered = filtered.filter((stock) => stock.group_id === selectedGroupId);
    }

    // Filter by search keyword
    if (searchKeyword.trim()) {
      const keyword = searchKeyword.toLowerCase();
      filtered = filtered.filter(
        (stock) =>
          stock.stock_code.toLowerCase().includes(keyword) ||
          stock.stock_name.toLowerCase().includes(keyword) ||
          stock.note?.toLowerCase().includes(keyword)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let compareValue = 0;

      switch (sortBy) {
        case 'code':
          compareValue = a.stock_code.localeCompare(b.stock_code);
          break;
        case 'name':
          compareValue = a.stock_name.localeCompare(b.stock_name);
          break;
        case 'created_at':
          compareValue = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
      }

      return sortOrder === 'asc' ? compareValue : -compareValue;
    });

    return filtered;
  },
}));
