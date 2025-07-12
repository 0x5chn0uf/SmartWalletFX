import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClient from '../services/api';
import { UserProfile } from './authSlice';

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
      const resp = await apiClient.post('/auth/verify-email', { token }, { withCredentials: true });
      const { access_token: accessToken, refresh_token: refreshToken } = resp.data as {
        access_token: string;
        refresh_token: string;
      };

      if (accessToken) {
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
        localStorage.setItem('access_token', accessToken);
      }
      if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken);
      }

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
      .addCase(verifyEmail.fulfilled, (state, action) => {
        state.status = 'succeeded';
        // Successful verification also implies authentication
        // We don't manage auth state here (handled in authSlice), but keeping for completeness
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
