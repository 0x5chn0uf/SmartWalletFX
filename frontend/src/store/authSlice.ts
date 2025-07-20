import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import apiClient from '../services/api';
import { verifyEmail } from './emailVerificationSlice';

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  email_verified: boolean;
  role?: string;
}

export interface AuthError {
  status?: number | null;
  data?: any;
  message?: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: AuthError | null;
}

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  status: 'idle',
  error: null,
};

export const fetchCurrentUser = createAsyncThunk('auth/fetchCurrentUser', async () => {
  const resp = await apiClient.get('/users/me', { withCredentials: true });
  // mark session present
  localStorage.setItem('session_active', '1');
  return resp.data as UserProfile;
});

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    const form = new URLSearchParams();
    form.append('username', credentials.email);
    form.append('password', credentials.password);
    try {
      const tokenResp = await apiClient.post('/auth/token', form, { withCredentials: true });
      const accessToken = tokenResp.data?.access_token as string | undefined;
      if (accessToken) {
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
        localStorage.setItem('access_token', accessToken);
      }
      const resp = await apiClient.get('/users/me', { withCredentials: true });
      // mark session present
      localStorage.setItem('session_active', '1');
      return resp.data as UserProfile;
    } catch (err: any) {
      if (axios.isAxiosError(err)) {
        return rejectWithValue({
          status: err.response?.status,
          data: err.response?.data,
        });
      }
      throw err;
    }
  }
);

export const registerUser = createAsyncThunk(
  'auth/register',
  async (payload: { email: string; password: string }, { rejectWithValue }) => {
    try {
      await apiClient.post(
        '/auth/register',
        {
          username: payload.email.split('@')[0],
          email: payload.email,
          password: payload.password,
        },
        { withCredentials: true }
      );
    } catch (err: any) {
      if (axios.isAxiosError(err)) {
        return rejectWithValue({
          status: err.response?.status,
          data: err.response?.data,
        });
      }
      throw err;
    }
  }
);

export const logoutUser = createAsyncThunk('auth/logout', async () => {
  try {
    await apiClient.post('/auth/logout', {}, { withCredentials: true });
  } catch (error) {
    // Even if backend logout fails, clear frontend state
    console.warn('Backend logout failed, clearing frontend state anyway:', error);
  }
  delete apiClient.defaults.headers.common['Authorization'];
  localStorage.removeItem('session_active');
  localStorage.removeItem('access_token');
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: state => {
      state.isAuthenticated = false;
      state.user = null;
      state.status = 'idle';
      state.error = null;
    },
    sessionCheckFinished: state => {
      // Silent session check completed and no session was found.
      state.status = 'failed';
    },
    sessionCheckStarted: state => {
      state.status = 'loading';
    },
  },
  extraReducers: builder => {
    builder
      .addCase(login.pending, state => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.isAuthenticated = true;
        state.user = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.status = 'failed';
        state.error = (action.payload as AuthError) || {
          message: action.error.message || 'Login failed',
        };
      })
      .addCase(registerUser.pending, state => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(registerUser.fulfilled, state => {
        state.status = 'succeeded';
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.status = 'failed';
        state.error = (action.payload as AuthError) || {
          message: action.error.message || 'Registration failed',
        };
      })
      .addCase(fetchCurrentUser.pending, state => {
        state.status = 'loading';
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.isAuthenticated = true;
        state.user = action.payload;
        state.status = 'succeeded';
      })
      .addCase(fetchCurrentUser.rejected, state => {
        state.status = 'failed';
      })
      // Mark authenticated on successful email verification (auto-login)
      .addCase(verifyEmail.fulfilled, (state, action) => {
        state.isAuthenticated = true;
        state.user = action.payload;
        state.status = 'succeeded';
      })
      .addCase(logoutUser.fulfilled, state => {
        state.isAuthenticated = false;
        state.user = null;
        state.status = 'idle';
      })
      .addCase(logoutUser.rejected, state => {
        // Even if logout fails, clear frontend state
        state.isAuthenticated = false;
        state.user = null;
        state.status = 'idle';
      });
  },
});

export const { logout, sessionCheckFinished, sessionCheckStarted } = authSlice.actions;

export default authSlice.reducer;
