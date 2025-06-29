import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClient from '../services/api';

interface Wallet {
  id: string;
  name: string;
  balance: number;
}

interface Overview {
  totalWallets: number;
  totalBalance: number;
  dailyVolume: number;
  chart: Array<{ date: string; balance: number }>;
  portfolioDistribution: Wallet[];
}

interface DashboardState {
  overview: Overview | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: DashboardState = {
  overview: null,
  status: 'idle',
  error: null,
};

export const fetchDashboardOverview = createAsyncThunk('dashboard/fetchOverview', async () => {
  const res = await apiClient.get<Overview>('/dashboard/overview');
  return res.data;
});

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {},
  extraReducers: builder => {
    builder
      .addCase(fetchDashboardOverview.pending, state => {
        state.status = 'loading';
      })
      .addCase(fetchDashboardOverview.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.overview = action.payload;
      })
      .addCase(fetchDashboardOverview.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'failed to load';
      });
  },
});

export default dashboardSlice.reducer;
