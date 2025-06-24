import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClient from '../services/api';

interface Wallet {
  id: string;
  name: string;
  address: string;
  balance: number;
  currency: string;
  lastUpdated: string;
}

interface WalletsResponse {
  wallets: Wallet[];
  total: number;
  page: number;
  limit: number;
}

interface WalletsState {
  wallets: Wallet[];
  total: number;
  page: number;
  limit: number;
  search: string;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: WalletsState = {
  wallets: [],
  total: 0,
  page: 1,
  limit: 10,
  search: '',
  status: 'idle',
  error: null,
};

export const fetchWallets = createAsyncThunk(
  'wallets/fetchWallets',
  async ({ page, limit, search }: { page: number; limit: number; search: string }) => {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...(search && { search }),
    });
    const res = await apiClient.get<WalletsResponse>(`/wallets?${params}`);
    return res.data;
  }
);

const walletsSlice = createSlice({
  name: 'wallets',
  initialState,
  reducers: {
    setSearch: (state, action) => {
      state.search = action.payload;
      state.page = 1; // Reset to first page on search
    },
    setPage: (state, action) => {
      state.page = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchWallets.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchWallets.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.wallets = action.payload.wallets;
        state.total = action.payload.total;
        state.page = action.payload.page;
        state.limit = action.payload.limit;
      })
      .addCase(fetchWallets.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to fetch wallets';
      });
  },
});

export const { setSearch, setPage } = walletsSlice.actions;
export default walletsSlice.reducer; 