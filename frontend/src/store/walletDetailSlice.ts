import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClient from '../services/api';

export interface Transaction {
  id: string;
  date: string;
  type: 'deposit' | 'withdraw' | 'trade';
  amount: number;
  currency: string;
  balanceAfter: number;
}

export interface WalletDetail {
  id: string;
  name: string;
  address: string;
  balance: number;
  currency: string;
  lastUpdated: string;
  trend: { date: string; balance: number }[];
}

interface WalletDetailState {
  wallet: WalletDetail | null;
  transactions: Transaction[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: WalletDetailState = {
  wallet: null,
  transactions: [],
  status: 'idle',
  error: null,
};

export const fetchWalletDetail = createAsyncThunk(
  'walletDetail/fetchWalletDetail',
  async (walletId: string) => {
    const res = await apiClient.get<WalletDetail>(`/wallets/${walletId}`);
    return res.data;
  }
);

export const fetchWalletTransactions = createAsyncThunk(
  'walletDetail/fetchWalletTransactions',
  async (walletId: string) => {
    const res = await apiClient.get<Transaction[]>(`/wallets/${walletId}/transactions`);
    return res.data;
  }
);

const walletDetailSlice = createSlice({
  name: 'walletDetail',
  initialState,
  reducers: {
    clearWalletDetail: state => {
      state.wallet = null;
      state.transactions = [];
      state.status = 'idle';
      state.error = null;
    },
  },
  extraReducers: builder => {
    builder
      .addCase(fetchWalletDetail.pending, state => {
        state.status = 'loading';
      })
      .addCase(fetchWalletDetail.fulfilled, (state, action) => {
        state.wallet = action.payload;
        state.status = 'succeeded';
      })
      .addCase(fetchWalletDetail.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to fetch wallet details';
      })
      .addCase(fetchWalletTransactions.pending, state => {
        state.status = 'loading';
      })
      .addCase(fetchWalletTransactions.fulfilled, (state, action) => {
        state.transactions = action.payload;
        state.status = 'succeeded';
      })
      .addCase(fetchWalletTransactions.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to fetch transactions';
      });
  },
});

export const { clearWalletDetail } = walletDetailSlice.actions;
export default walletDetailSlice.reducer;
