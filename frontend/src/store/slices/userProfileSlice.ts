import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import apiClient from '../../services/api';
import {
  validateApiResponse,
  ValidationError,
  formatValidationError,
} from '../../utils/validation';
import {
  UserProfileSchema,
  UserProfileUpdate,
  PasswordChange,
  NotificationPreferences,
  type UserProfile,
} from '../../schemas/api';

interface UserProfileState {
  loading: boolean;
  error: string | null;
  success: boolean;
}

const initialState: UserProfileState = {
  loading: false,
  error: null,
  success: false,
};

// Update user profile
export const updateUserProfile = createAsyncThunk(
  'userProfile/updateProfile',
  async (profileData: UserProfileUpdate, { rejectWithValue }) => {
    try {
      const resp = await apiClient.put('/users/me/profile', profileData, {
        withCredentials: true,
      });

      // Validate the response using zod schema
      const validatedData = validateApiResponse(resp, UserProfileSchema);
      return validatedData;
    } catch (err: any) {
      if (err instanceof ValidationError) {
        console.error('Validation error in updateUserProfile:', formatValidationError(err));
        return rejectWithValue(formatValidationError(err));
      }
      if (axios.isAxiosError(err)) {
        return rejectWithValue(err.response?.data?.detail || 'Failed to update profile');
      }
      throw err;
    }
  }
);

// Change password
export const changePassword = createAsyncThunk(
  'userProfile/changePassword',
  async (passwordData: PasswordChange, { rejectWithValue }) => {
    try {
      await apiClient.post('/users/me/change-password', passwordData, {
        withCredentials: true,
      });
      return { message: 'Password changed successfully' };
    } catch (err: any) {
      if (axios.isAxiosError(err)) {
        return rejectWithValue(err.response?.data?.detail || 'Failed to change password');
      }
      throw err;
    }
  }
);

// Update notification preferences
export const updateNotificationPreferences = createAsyncThunk(
  'userProfile/updateNotifications',
  async (preferences: NotificationPreferences, { rejectWithValue }) => {
    try {
      const resp = await apiClient.put('/users/me/notifications', preferences, {
        withCredentials: true,
      });

      // Validate the response using zod schema
      const validatedData = validateApiResponse(resp, UserProfileSchema);
      return validatedData;
    } catch (err: any) {
      if (err instanceof ValidationError) {
        console.error(
          'Validation error in updateNotificationPreferences:',
          formatValidationError(err)
        );
        return rejectWithValue(formatValidationError(err));
      }
      if (axios.isAxiosError(err)) {
        return rejectWithValue(
          err.response?.data?.detail || 'Failed to update notification preferences'
        );
      }
      throw err;
    }
  }
);

// Upload profile picture
export const uploadProfilePicture = createAsyncThunk(
  'userProfile/uploadProfilePicture',
  async (formData: FormData, { rejectWithValue }) => {
    try {
      const resp = await apiClient.post('/users/me/profile/picture', formData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Validate the response using zod schema
      const validatedData = validateApiResponse(resp, UserProfileSchema);
      return validatedData;
    } catch (err: any) {
      if (err instanceof ValidationError) {
        console.error('Validation error in uploadProfilePicture:', formatValidationError(err));
        return rejectWithValue(formatValidationError(err));
      }
      if (axios.isAxiosError(err)) {
        return rejectWithValue(err.response?.data?.detail || 'Failed to upload profile picture');
      }
      throw err;
    }
  }
);

// Delete profile picture
export const deleteProfilePicture = createAsyncThunk(
  'userProfile/deleteProfilePicture',
  async (_, { rejectWithValue }) => {
    try {
      const resp = await apiClient.delete('/users/me/profile/picture', {
        withCredentials: true,
      });

      // Validate the response using zod schema
      const validatedData = validateApiResponse(resp, UserProfileSchema);
      return validatedData;
    } catch (err: any) {
      if (err instanceof ValidationError) {
        console.error('Validation error in deleteProfilePicture:', formatValidationError(err));
        return rejectWithValue(formatValidationError(err));
      }
      if (axios.isAxiosError(err)) {
        return rejectWithValue(err.response?.data?.detail || 'Failed to delete profile picture');
      }
      throw err;
    }
  }
);

// Delete account
export const deleteAccount = createAsyncThunk(
  'userProfile/deleteAccount',
  async (data: { password: string }, { rejectWithValue }) => {
    try {
      await apiClient.delete('/users/me', {
        data: { password: data.password },
        withCredentials: true,
      });
      return { message: 'Account deleted successfully' };
    } catch (err: any) {
      if (axios.isAxiosError(err)) {
        return rejectWithValue(err.response?.data?.detail || 'Failed to delete account');
      }
      throw err;
    }
  }
);

const userProfileSlice = createSlice({
  name: 'userProfile',
  initialState,
  reducers: {
    clearMessages: state => {
      state.error = null;
      state.success = false;
    },
    setSuccess: (state, action) => {
      state.success = action.payload;
      state.error = null;
    },
  },
  extraReducers: builder => {
    builder
      // Update profile
      .addCase(updateUserProfile.pending, state => {
        state.loading = true;
        state.error = null;
        state.success = false;
      })
      .addCase(updateUserProfile.fulfilled, state => {
        state.loading = false;
        state.success = true;
        state.error = null;
      })
      .addCase(updateUserProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.success = false;
      })

      // Change password
      .addCase(changePassword.pending, state => {
        state.loading = true;
        state.error = null;
        state.success = false;
      })
      .addCase(changePassword.fulfilled, state => {
        state.loading = false;
        state.success = true;
        state.error = null;
      })
      .addCase(changePassword.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.success = false;
      })

      // Update notification preferences
      .addCase(updateNotificationPreferences.pending, state => {
        state.loading = true;
        state.error = null;
        state.success = false;
      })
      .addCase(updateNotificationPreferences.fulfilled, state => {
        state.loading = false;
        state.success = true;
        state.error = null;
      })
      .addCase(updateNotificationPreferences.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.success = false;
      })

      // Upload profile picture
      .addCase(uploadProfilePicture.pending, state => {
        state.loading = true;
        state.error = null;
        state.success = false;
      })
      .addCase(uploadProfilePicture.fulfilled, state => {
        state.loading = false;
        state.success = true;
        state.error = null;
      })
      .addCase(uploadProfilePicture.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.success = false;
      })

      // Delete profile picture
      .addCase(deleteProfilePicture.pending, state => {
        state.loading = true;
        state.error = null;
        state.success = false;
      })
      .addCase(deleteProfilePicture.fulfilled, state => {
        state.loading = false;
        state.success = true;
        state.error = null;
      })
      .addCase(deleteProfilePicture.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.success = false;
      })

      // Delete account
      .addCase(deleteAccount.pending, state => {
        state.loading = true;
        state.error = null;
        state.success = false;
      })
      .addCase(deleteAccount.fulfilled, state => {
        state.loading = false;
        state.success = true;
        state.error = null;
      })
      .addCase(deleteAccount.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.success = false;
      });
  },
});

export const { clearMessages, setSuccess } = userProfileSlice.actions;
export default userProfileSlice.reducer;
