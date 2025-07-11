import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClient from '../services/api';

interface VerificationState {
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: VerificationState = {
  status: 'idle',
  error: null,
};

export const verifyEmail = createAsyncThunk('emailVerification/verify', async (token: string) => {
  await apiClient.post('/auth/verify-email', { token });
});

export const resendVerification = createAsyncThunk(
  'emailVerification/resend',
  async (email: string) => {
    await apiClient.post('/auth/resend-verification', { email });
  }
);

const slice = createSlice({
  name: 'emailVerification',
  initialState,
  reducers: {},
  extraReducers: builder => {
    builder
      .addCase(verifyEmail.pending, state => {
        state.status = 'loading';
      })
      .addCase(verifyEmail.fulfilled, state => {
        state.status = 'succeeded';
      })
      .addCase(verifyEmail.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Verification failed';
      })
      .addCase(resendVerification.pending, state => {
        state.status = 'loading';
      })
      .addCase(resendVerification.fulfilled, state => {
        state.status = 'succeeded';
      })
      .addCase(resendVerification.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Resend failed';
      });
  },
});

export default slice.reducer;
