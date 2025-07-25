import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import apiClient from '../services/api';
import { verifyEmail } from './emailVerificationSlice';
import {
  updateUserProfile,
  updateNotificationPreferences,
  uploadProfilePicture,
  deleteProfilePicture,
} from './slices/userProfileSlice';
import { validateApiResponse, ValidationError, formatValidationError } from '../utils/validation';
import {
  UserProfileSchema,
  TokenResponseSchema,
  type UserProfile,
  type AuthError,
} from '../schemas/api';

// UserProfile and AuthError types are now imported from schemas/api.ts

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

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const resp = await apiClient.get('/users/me', { withCredentials: true });

      // Validate the response using zod schema
      const validatedData = validateApiResponse(resp, UserProfileSchema);

      // mark session present
      localStorage.setItem('session_active', '1');
      return validatedData;
    } catch (err: any) {
      if (err instanceof ValidationError) {
        console.error('Validation error in fetchCurrentUser:', formatValidationError(err));
        return rejectWithValue({
          status: err.response.status,
          data: err.response.data,
          message: formatValidationError(err),
        });
      }
      if (axios.isAxiosError(err)) {
        return rejectWithValue({
          status: err.response?.status,
          data: err.response?.data,
          message: 'Failed to fetch user profile',
        });
      }
      throw err;
    }
  }
);

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    const form = new URLSearchParams();
    form.append('username', credentials.email);
    form.append('password', credentials.password);
    try {
      // Login request - tokens will be set as httpOnly cookies by the backend
      await apiClient.post('/auth/token', form, { withCredentials: true });

      // Fetch user profile to confirm authentication and populate state
      const resp = await apiClient.get('/users/me', { withCredentials: true });

      // Validate user profile response
      const validatedUserData = validateApiResponse(resp, UserProfileSchema);

      // mark session present for refresh token logic
      localStorage.setItem('session_active', '1');
      return validatedUserData;
    } catch (err: any) {
      if (err instanceof ValidationError) {
        console.error('Validation error in login:', formatValidationError(err));
        return rejectWithValue({
          status: err.response.status,
          data: err.response.data,
          message: formatValidationError(err),
        });
      }
      if (axios.isAxiosError(err)) {
        return rejectWithValue({
          status: err.response?.status,
          data: err.response?.data,
          message: 'Login failed',
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
  // Clear session flag - cookies will be cleared by the backend
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
      })
      // Sync user data when profile updates succeed
      .addCase(updateUserProfile.fulfilled, (state, action) => {
        if (state.user) {
          state.user = { ...state.user, ...action.payload };
        }
      })
      .addCase(updateNotificationPreferences.fulfilled, (state, action) => {
        if (state.user) {
          state.user = { ...state.user, ...action.payload };
        }
      })
      .addCase(uploadProfilePicture.fulfilled, (state, action) => {
        if (state.user) {
          state.user = { ...state.user, ...action.payload };
        }
      })
      .addCase(deleteProfilePicture.fulfilled, (state, action) => {
        if (state.user) {
          state.user = { ...state.user, ...action.payload };
        }
      });
  },
});

export const { logout, sessionCheckFinished, sessionCheckStarted } = authSlice.actions;

export default authSlice.reducer;
