import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClient from '../services/api';
import { type UserProfile } from '../schemas/api';

interface VerificationState {
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: VerificationState = {
  status: 'idle',
  error: null,
};

export const verifyEmail = createAsyncThunk(
  'emailVerification/verify',
  async (token: string, { rejectWithValue }) => {
    try {
      // Email verification request - tokens will be set as httpOnly cookies by the backend
      await apiClient.post('/auth/verify-email', { token }, { withCredentials: true });

      // Fetch user profile to update auth state
      const meResp = await apiClient.get('/users/me', { withCredentials: true });
      localStorage.setItem('session_active', '1');
      return meResp.data as UserProfile;
    } catch (err: any) {
      return rejectWithValue(err.response?.data || 'Verification failed');
    }
  }
);

export const resendVerification = createAsyncThunk(
  'emailVerification/resend',
  async (email: string, { rejectWithValue }) => {
    try {
      await apiClient.post('/auth/resend-verification', { email });
      return { success: true };
    } catch (err: any) {
      return rejectWithValue(err.response?.data || 'Resend failed');
    }
  }
);

const slice = createSlice({
  name: 'emailVerification',
  initialState,
  reducers: {
    resetState: () => initialState,
  },
  extraReducers: builder => {
    builder
      .addCase(verifyEmail.pending, state => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(verifyEmail.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.error = null;
        // Successful verification also implies authentication
        // We don't manage auth state here (handled in authSlice), but keeping for completeness
      })
      .addCase(verifyEmail.rejected, (state, action) => {
        state.status = 'failed';
        state.error = 'Verification failed';
      })
      .addCase(resendVerification.pending, state => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(resendVerification.fulfilled, state => {
        state.status = 'succeeded';
        state.error = null;
      })
      .addCase(resendVerification.rejected, (state, action) => {
        state.status = 'failed';
        state.error = 'Resend failed';
      });
  },
});

export default slice.reducer;
