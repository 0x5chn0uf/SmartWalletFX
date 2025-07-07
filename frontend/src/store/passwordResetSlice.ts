import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClient from '../services/api';

interface ResetState {
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: ResetState = {
  status: 'idle',
  error: null,
};

export const requestReset = createAsyncThunk('passwordReset/request', async (email: string) => {
  await apiClient.post('/auth/forgot-password', { email });
});

export const resetPassword = createAsyncThunk(
  'passwordReset/reset',
  async (payload: { token: string; password: string }) => {
    await apiClient.post('/auth/reset-password', payload);
  }
);

const slice = createSlice({
  name: 'passwordReset',
  initialState,
  reducers: {},
  extraReducers: builder => {
    builder
      .addCase(requestReset.pending, state => {
        state.status = 'loading';
      })
      .addCase(requestReset.fulfilled, state => {
        state.status = 'succeeded';
      })
      .addCase(requestReset.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Request failed';
      })
      .addCase(resetPassword.pending, state => {
        state.status = 'loading';
      })
      .addCase(resetPassword.fulfilled, state => {
        state.status = 'succeeded';
      })
      .addCase(resetPassword.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Reset failed';
      });
  },
});

export default slice.reducer;
