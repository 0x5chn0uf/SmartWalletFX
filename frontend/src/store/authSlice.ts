import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClient from '../services/api';

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  role?: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
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
  async (credentials: { email: string; password: string }) => {
    const form = new URLSearchParams();
    form.append('username', credentials.email);
    form.append('password', credentials.password);
    const tokenResp = await apiClient.post('/auth/token', form, { withCredentials: true });
    const accessToken = tokenResp.data?.access_token as string | undefined;
    if (accessToken) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    }
    const resp = await apiClient.get('/users/me', { withCredentials: true });
    // mark session present
    localStorage.setItem('session_active', '1');
    return resp.data as UserProfile;
  }
);

export const registerUser = createAsyncThunk(
  'auth/register',
  async (payload: { email: string; password: string }) => {
    await apiClient.post(
      '/auth/register',
      {
        username: payload.email.split('@')[0],
        email: payload.email,
        password: payload.password,
      },
      { withCredentials: true }
    );
    const form = new URLSearchParams();
    form.append('username', payload.email);
    form.append('password', payload.password);
    const tokenResp = await apiClient.post('/auth/token', form, { withCredentials: true });
    const accessToken = tokenResp.data?.access_token as string | undefined;
    if (accessToken) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    }
    const resp = await apiClient.get('/users/me', { withCredentials: true });
    // mark session present
    localStorage.setItem('session_active', '1');
    return resp.data as UserProfile;
  }
);

export const logoutUser = createAsyncThunk('auth/logout', async () => {
  await apiClient.post('/auth/logout', {}, { withCredentials: true });
  delete apiClient.defaults.headers.common['Authorization'];
  localStorage.removeItem('session_active');
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
        state.error = action.error.message || 'Login failed';
      })
      .addCase(registerUser.pending, state => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isAuthenticated = true;
        state.user = action.payload;
        state.status = 'succeeded';
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Registration failed';
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
        state.status = 'idle';
      })
      .addCase(logoutUser.fulfilled, state => {
        state.isAuthenticated = false;
        state.user = null;
        state.status = 'idle';
      });
  },
});

export const { logout } = authSlice.actions;

export default authSlice.reducer;
