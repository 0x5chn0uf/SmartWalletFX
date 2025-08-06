import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClient from '../services/api';

interface ResetState {
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  tokenValidationStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: ResetState = {
  status: 'idle',
  tokenValidationStatus: 'idle',
  error: null,
};

export const requestReset = createAsyncThunk(
  'passwordReset/request',
  async (email: string, { rejectWithValue }) => {
    try {
      await apiClient.post('/auth/password-reset-request', { email });
      return { success: true };
    } catch (error: any) {
      if (error.response?.status === 429) {
        return rejectWithValue('Too many password reset requests. Please try again later.');
      }
      if (error.code === 'NETWORK_ERROR' || !error.response) {
        return rejectWithValue('Network error. Please check your connection and try again.');
      }
      return rejectWithValue(
        error.response?.data?.detail || 'Something went wrong. Please try again.'
      );
    }
  }
);

export const verifyResetToken = createAsyncThunk(
  'passwordReset/verifyToken',
  async (token: string, { rejectWithValue }) => {
    try {
      await apiClient.post('/auth/password-reset-verify', { token });
      return { success: true };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Invalid or expired token');
    }
  }
);

export const resetPassword = createAsyncThunk(
  'passwordReset/reset',
  async (payload: { token: string; password: string }, { rejectWithValue }) => {
    try {
      await apiClient.post('/auth/password-reset-complete', payload);
      return { success: true };
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.detail || 'Failed to reset password. Please try again.'
      );
    }
  }
);

const slice = createSlice({
  name: 'passwordReset',
  initialState,
  reducers: {
    resetState: state => {
      state.status = 'idle';
      state.tokenValidationStatus = 'idle';
      state.error = null;
    },
  },
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
        state.error = (action.payload as string) || action.error.message || 'Request failed';
      })
      .addCase(resetPassword.pending, state => {
        state.status = 'loading';
      })
      .addCase(resetPassword.fulfilled, state => {
        state.status = 'succeeded';
      })
      .addCase(resetPassword.rejected, (state, action) => {
        state.status = 'failed';
        state.error = (action.payload as string) || action.error.message || 'Reset failed';
      })
      .addCase(verifyResetToken.pending, state => {
        state.tokenValidationStatus = 'loading';
        state.error = null;
      })
      .addCase(verifyResetToken.fulfilled, state => {
        state.tokenValidationStatus = 'succeeded';
        state.error = null;
      })
      .addCase(verifyResetToken.rejected, (state, action) => {
        state.tokenValidationStatus = 'failed';
        state.error =
          (action.payload as string) || action.error.message || 'Token validation failed';
      });
  },
});

export const { resetState } = slice.actions;
export default slice.reducer;
