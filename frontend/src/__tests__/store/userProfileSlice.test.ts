import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import userProfileReducer, {
  updateUserProfile,
  changePassword,
  updateNotificationPreferences,
  uploadProfilePicture,
  deleteProfilePicture,
  deleteAccount,
  clearMessages,
  setSuccess,
} from '../../store/slices/userProfileSlice';
import { ValidationError } from '../../utils/validation';

// Mock the API client
vi.mock('../../services/api', () => ({
  default: {
    put: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock the validation utilities
vi.mock('../../utils/validation', () => ({
  validateApiResponse: vi.fn(),
  ValidationError: class ValidationError extends Error {
    constructor(message: string) {
      super(message);
      this.name = 'ValidationError';
    }
  },
  formatValidationError: vi.fn(error => error.message),
}));

// Mock axios
vi.mock('axios', () => ({
  default: {
    isAxiosError: vi.fn(),
  },
}));

import apiClient from '../../services/api';
import { validateApiResponse, formatValidationError } from '../../utils/validation';
import axios from 'axios';

interface UserProfileState {
  loading: boolean;
  error: string | null;
  success: boolean;
}

describe('userProfileSlice', () => {
  let store: any;

  beforeEach(() => {
    vi.clearAllMocks();
    store = configureStore({
      reducer: {
        userProfile: userProfileReducer,
      },
    });
  });

  describe('initial state', () => {
    it('should return the initial state', () => {
      expect(userProfileReducer(undefined, { type: undefined })).toEqual({
        loading: false,
        error: null,
        success: false,
      });
    });
  });

  describe('synchronous actions', () => {
    describe('clearMessages', () => {
      it('should clear error and success messages', () => {
        const prevState: UserProfileState = {
          loading: false,
          error: 'Some error',
          success: true,
        };

        const result = userProfileReducer(prevState, clearMessages());

        expect(result).toEqual({
          loading: false,
          error: null,
          success: false,
        });
      });
    });

    describe('setSuccess', () => {
      it('should set success state and clear error', () => {
        const prevState: UserProfileState = {
          loading: false,
          error: 'Some error',
          success: false,
        };

        const result = userProfileReducer(prevState, setSuccess(true));

        expect(result).toEqual({
          loading: false,
          error: null,
          success: true,
        });
      });

      it('should set success to false', () => {
        const prevState: UserProfileState = {
          loading: false,
          error: null,
          success: true,
        };

        const result = userProfileReducer(prevState, setSuccess(false));

        expect(result).toEqual({
          loading: false,
          error: null,
          success: false,
        });
      });
    });
  });

  describe('updateUserProfile async thunk', () => {
    const mockProfileData = {
      first_name: 'John',
      last_name: 'Doe',
      bio: 'Test bio',
    };

    const mockValidatedResponse = {
      id: '1',
      username: 'johndoe',
      email: 'john@example.com',
      first_name: 'John',
      last_name: 'Doe',
      bio: 'Test bio',
    };

    it('should handle pending state', () => {
      const action = { type: updateUserProfile.pending.type };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: true,
        error: null,
        success: false,
      });
    });

    it('should handle fulfilled state', () => {
      const action = {
        type: updateUserProfile.fulfilled.type,
        payload: mockValidatedResponse,
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: null,
        success: true,
      });
    });

    it('should handle rejected state', () => {
      const action = {
        type: updateUserProfile.rejected.type,
        payload: 'Failed to update profile',
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: 'Failed to update profile',
        success: false,
      });
    });

    it('should make API call with correct parameters', async () => {
      const mockApiResponse = { data: mockValidatedResponse };
      (apiClient.put as any).mockResolvedValue(mockApiResponse);
      (validateApiResponse as any).mockReturnValue(mockValidatedResponse);

      await store.dispatch(updateUserProfile(mockProfileData));

      expect(apiClient.put).toHaveBeenCalledWith('/users/me/profile', mockProfileData, {
        withCredentials: true,
      });
      expect(validateApiResponse).toHaveBeenCalled();
    });

    it('should handle validation errors', async () => {
      const validationError = new ValidationError('Validation failed');
      (apiClient.put as any).mockRejectedValue(validationError);
      (formatValidationError as any).mockReturnValue('Validation failed');

      const result = await store.dispatch(updateUserProfile(mockProfileData));

      expect(result.type).toBe('userProfile/updateProfile/rejected');
      expect(result.payload).toBe('Validation failed');
    });

    it('should handle axios errors', async () => {
      const axiosError = {
        response: {
          data: {
            detail: 'Server error',
          },
        },
      };
      (apiClient.put as any).mockRejectedValue(axiosError);
      (axios.isAxiosError as any).mockReturnValue(true);

      const result = await store.dispatch(updateUserProfile(mockProfileData));

      expect(result.type).toBe('userProfile/updateProfile/rejected');
      expect(result.payload).toBe('Server error');
    });

    it('should handle axios errors without detail', async () => {
      const axiosError = {
        response: {
          data: {},
        },
      };
      (apiClient.put as any).mockRejectedValue(axiosError);
      (axios.isAxiosError as any).mockReturnValue(true);

      const result = await store.dispatch(updateUserProfile(mockProfileData));

      expect(result.type).toBe('userProfile/updateProfile/rejected');
      expect(result.payload).toBe('Failed to update profile');
    });
  });

  describe('changePassword async thunk', () => {
    const mockPasswordData = {
      current_password: 'oldpassword',
      new_password: 'newpassword123',
      confirm_password: 'newpassword123',
    };

    it('should handle pending state', () => {
      const action = { type: changePassword.pending.type };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: true,
        error: null,
        success: false,
      });
    });

    it('should handle fulfilled state', () => {
      const action = {
        type: changePassword.fulfilled.type,
        payload: { message: 'Password changed successfully' },
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: null,
        success: true,
      });
    });

    it('should handle rejected state', () => {
      const action = {
        type: changePassword.rejected.type,
        payload: 'Failed to change password',
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: 'Failed to change password',
        success: false,
      });
    });

    it('should make API call with correct parameters', async () => {
      (apiClient.post as any).mockResolvedValue({});

      await store.dispatch(changePassword(mockPasswordData));

      expect(apiClient.post).toHaveBeenCalledWith('/users/me/change-password', mockPasswordData, {
        withCredentials: true,
      });
    });

    it('should handle axios errors', async () => {
      const axiosError = {
        response: {
          data: {
            detail: 'Invalid current password',
          },
        },
      };
      (apiClient.post as any).mockRejectedValue(axiosError);
      (axios.isAxiosError as any).mockReturnValue(true);

      const result = await store.dispatch(changePassword(mockPasswordData));

      expect(result.type).toBe('userProfile/changePassword/rejected');
      expect(result.payload).toBe('Invalid current password');
    });
  });

  describe('updateNotificationPreferences async thunk', () => {
    const mockPreferences = {
      email_notifications: true,
      security_alerts: true,
      portfolio_updates: false,
      price_alerts: true,
    };

    const mockValidatedResponse = {
      id: '1',
      username: 'johndoe',
      email: 'john@example.com',
      notification_preferences: mockPreferences,
    };

    it('should handle pending state', () => {
      const action = { type: updateNotificationPreferences.pending.type };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: true,
        error: null,
        success: false,
      });
    });

    it('should handle fulfilled state', () => {
      const action = {
        type: updateNotificationPreferences.fulfilled.type,
        payload: mockValidatedResponse,
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: null,
        success: true,
      });
    });

    it('should handle rejected state', () => {
      const action = {
        type: updateNotificationPreferences.rejected.type,
        payload: 'Failed to update notification preferences',
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: 'Failed to update notification preferences',
        success: false,
      });
    });

    it('should make API call with correct parameters', async () => {
      const mockApiResponse = { data: mockValidatedResponse };
      (apiClient.put as any).mockResolvedValue(mockApiResponse);
      (validateApiResponse as any).mockReturnValue(mockValidatedResponse);

      await store.dispatch(updateNotificationPreferences(mockPreferences));

      expect(apiClient.put).toHaveBeenCalledWith('/users/me/notifications', mockPreferences, {
        withCredentials: true,
      });
      expect(validateApiResponse).toHaveBeenCalled();
    });

    it('should handle validation errors', async () => {
      const validationError = new ValidationError('Invalid preferences');
      (apiClient.put as any).mockRejectedValue(validationError);
      (formatValidationError as any).mockReturnValue('Invalid preferences');

      const result = await store.dispatch(updateNotificationPreferences(mockPreferences));

      expect(result.type).toBe('userProfile/updateNotifications/rejected');
      expect(result.payload).toBe('Invalid preferences');
    });
  });

  describe('uploadProfilePicture async thunk', () => {
    const mockFormData = new FormData();
    mockFormData.append('file', new File(['test'], 'test.jpg', { type: 'image/jpeg' }));

    const mockValidatedResponse = {
      id: '1',
      username: 'johndoe',
      email: 'john@example.com',
      profile_picture_url: 'https://example.com/picture.jpg',
    };

    it('should handle pending state', () => {
      const action = { type: uploadProfilePicture.pending.type };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: true,
        error: null,
        success: false,
      });
    });

    it('should handle fulfilled state', () => {
      const action = {
        type: uploadProfilePicture.fulfilled.type,
        payload: mockValidatedResponse,
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: null,
        success: true,
      });
    });

    it('should handle rejected state', () => {
      const action = {
        type: uploadProfilePicture.rejected.type,
        payload: 'Failed to upload profile picture',
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: 'Failed to upload profile picture',
        success: false,
      });
    });

    it('should make API call with correct parameters', async () => {
      const mockApiResponse = { data: mockValidatedResponse };
      (apiClient.post as any).mockResolvedValue(mockApiResponse);
      (validateApiResponse as any).mockReturnValue(mockValidatedResponse);

      await store.dispatch(uploadProfilePicture(mockFormData));

      expect(apiClient.post).toHaveBeenCalledWith('/users/me/profile/picture', mockFormData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      expect(validateApiResponse).toHaveBeenCalled();
    });

    it('should handle validation errors', async () => {
      const validationError = new ValidationError('Invalid file format');
      (apiClient.post as any).mockRejectedValue(validationError);
      (formatValidationError as any).mockReturnValue('Invalid file format');

      const result = await store.dispatch(uploadProfilePicture(mockFormData));

      expect(result.type).toBe('userProfile/uploadProfilePicture/rejected');
      expect(result.payload).toBe('Invalid file format');
    });

    it('should handle axios errors', async () => {
      const axiosError = {
        response: {
          data: {
            detail: 'File too large',
          },
        },
      };
      (apiClient.post as any).mockRejectedValue(axiosError);
      (axios.isAxiosError as any).mockReturnValue(true);

      const result = await store.dispatch(uploadProfilePicture(mockFormData));

      expect(result.type).toBe('userProfile/uploadProfilePicture/rejected');
      expect(result.payload).toBe('File too large');
    });
  });

  describe('deleteProfilePicture async thunk', () => {
    const mockValidatedResponse = {
      id: '1',
      username: 'johndoe',
      email: 'john@example.com',
      profile_picture_url: null,
    };

    it('should handle pending state', () => {
      const action = { type: deleteProfilePicture.pending.type };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: true,
        error: null,
        success: false,
      });
    });

    it('should handle fulfilled state', () => {
      const action = {
        type: deleteProfilePicture.fulfilled.type,
        payload: mockValidatedResponse,
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: null,
        success: true,
      });
    });

    it('should handle rejected state', () => {
      const action = {
        type: deleteProfilePicture.rejected.type,
        payload: 'Failed to delete profile picture',
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: 'Failed to delete profile picture',
        success: false,
      });
    });

    it('should make API call with correct parameters', async () => {
      const mockApiResponse = { data: mockValidatedResponse };
      (apiClient.delete as any).mockResolvedValue(mockApiResponse);
      (validateApiResponse as any).mockReturnValue(mockValidatedResponse);

      await store.dispatch(deleteProfilePicture());

      expect(apiClient.delete).toHaveBeenCalledWith('/users/me/profile/picture', {
        withCredentials: true,
      });
      expect(validateApiResponse).toHaveBeenCalled();
    });

    it('should handle validation errors', async () => {
      const validationError = new ValidationError('Validation failed');
      (apiClient.delete as any).mockRejectedValue(validationError);
      (formatValidationError as any).mockReturnValue('Validation failed');

      const result = await store.dispatch(deleteProfilePicture());

      expect(result.type).toBe('userProfile/deleteProfilePicture/rejected');
      expect(result.payload).toBe('Validation failed');
    });

    it('should handle axios errors', async () => {
      const axiosError = {
        response: {
          data: {
            detail: 'Picture not found',
          },
        },
      };
      (apiClient.delete as any).mockRejectedValue(axiosError);
      (axios.isAxiosError as any).mockReturnValue(true);

      const result = await store.dispatch(deleteProfilePicture());

      expect(result.type).toBe('userProfile/deleteProfilePicture/rejected');
      expect(result.payload).toBe('Picture not found');
    });
  });

  describe('deleteAccount async thunk', () => {
    const mockPasswordData = { password: 'mypassword123' };

    it('should handle pending state', () => {
      const action = { type: deleteAccount.pending.type };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: true,
        error: null,
        success: false,
      });
    });

    it('should handle fulfilled state', () => {
      const action = {
        type: deleteAccount.fulfilled.type,
        payload: { message: 'Account deleted successfully' },
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: null,
        success: true,
      });
    });

    it('should handle rejected state', () => {
      const action = {
        type: deleteAccount.rejected.type,
        payload: 'Failed to delete account',
      };
      const result = userProfileReducer(undefined, action);

      expect(result).toEqual({
        loading: false,
        error: 'Failed to delete account',
        success: false,
      });
    });

    it('should make API call with correct parameters', async () => {
      (apiClient.delete as any).mockResolvedValue({});

      await store.dispatch(deleteAccount(mockPasswordData));

      expect(apiClient.delete).toHaveBeenCalledWith('/users/me', {
        data: { password: 'mypassword123' },
        withCredentials: true,
      });
    });

    it('should handle axios errors', async () => {
      const axiosError = {
        response: {
          data: {
            detail: 'Invalid password',
          },
        },
      };
      (apiClient.delete as any).mockRejectedValue(axiosError);
      (axios.isAxiosError as any).mockReturnValue(true);

      const result = await store.dispatch(deleteAccount(mockPasswordData));

      expect(result.type).toBe('userProfile/deleteAccount/rejected');
      expect(result.payload).toBe('Invalid password');
    });

    it('should handle axios errors without detail', async () => {
      const axiosError = {
        response: {
          data: {},
        },
      };
      (apiClient.delete as any).mockRejectedValue(axiosError);
      (axios.isAxiosError as any).mockReturnValue(true);

      const result = await store.dispatch(deleteAccount(mockPasswordData));

      expect(result.type).toBe('userProfile/deleteAccount/rejected');
      expect(result.payload).toBe('Failed to delete account');
    });
  });

  describe('error handling edge cases', () => {
    it('should rethrow non-axios and non-validation errors in updateUserProfile', async () => {
      const genericError = new Error('Generic error');
      (apiClient.put as any).mockRejectedValue(genericError);
      (axios.isAxiosError as any).mockReturnValue(false);

      const result = await store.dispatch(updateUserProfile({ first_name: 'John' }));
      expect(result.type).toBe('userProfile/updateProfile/rejected');
      expect(result.error.message).toBe('Generic error');
    });

    it('should rethrow non-axios errors in changePassword', async () => {
      const genericError = new Error('Generic error');
      (apiClient.post as any).mockRejectedValue(genericError);
      (axios.isAxiosError as any).mockReturnValue(false);

      const result = await store.dispatch(
        changePassword({
          current_password: 'old',
          new_password: 'new',
          confirm_password: 'new',
        })
      );
      expect(result.type).toBe('userProfile/changePassword/rejected');
      expect(result.error.message).toBe('Generic error');
    });

    it('should rethrow non-axios and non-validation errors in updateNotificationPreferences', async () => {
      const genericError = new Error('Generic error');
      (apiClient.put as any).mockRejectedValue(genericError);
      (axios.isAxiosError as any).mockReturnValue(false);

      const result = await store.dispatch(
        updateNotificationPreferences({
          email_notifications: true,
        })
      );
      expect(result.type).toBe('userProfile/updateNotifications/rejected');
      expect(result.error.message).toBe('Generic error');
    });

    it('should rethrow non-axios and non-validation errors in uploadProfilePicture', async () => {
      const genericError = new Error('Generic error');
      (apiClient.post as any).mockRejectedValue(genericError);
      (axios.isAxiosError as any).mockReturnValue(false);

      const formData = new FormData();
      const result = await store.dispatch(uploadProfilePicture(formData));
      expect(result.type).toBe('userProfile/uploadProfilePicture/rejected');
      expect(result.error.message).toBe('Generic error');
    });

    it('should rethrow non-axios and non-validation errors in deleteProfilePicture', async () => {
      const genericError = new Error('Generic error');
      (apiClient.delete as any).mockRejectedValue(genericError);
      (axios.isAxiosError as any).mockReturnValue(false);

      const result = await store.dispatch(deleteProfilePicture());
      expect(result.type).toBe('userProfile/deleteProfilePicture/rejected');
      expect(result.error.message).toBe('Generic error');
    });

    it('should rethrow non-axios errors in deleteAccount', async () => {
      const genericError = new Error('Generic error');
      (apiClient.delete as any).mockRejectedValue(genericError);
      (axios.isAxiosError as any).mockReturnValue(false);

      const result = await store.dispatch(deleteAccount({ password: 'test' }));
      expect(result.type).toBe('userProfile/deleteAccount/rejected');
      expect(result.error.message).toBe('Generic error');
    });
  });

  describe('state transitions', () => {
    it('should handle multiple actions in sequence', () => {
      let state = userProfileReducer(undefined, { type: updateUserProfile.pending.type });
      expect(state.loading).toBe(true);
      expect(state.error).toBe(null);
      expect(state.success).toBe(false);

      state = userProfileReducer(state, {
        type: updateUserProfile.rejected.type,
        payload: 'Error occurred',
      });
      expect(state.loading).toBe(false);
      expect(state.error).toBe('Error occurred');
      expect(state.success).toBe(false);

      state = userProfileReducer(state, clearMessages());
      expect(state.loading).toBe(false);
      expect(state.error).toBe(null);
      expect(state.success).toBe(false);

      state = userProfileReducer(state, { type: changePassword.pending.type });
      expect(state.loading).toBe(true);
      expect(state.error).toBe(null);
      expect(state.success).toBe(false);

      state = userProfileReducer(state, {
        type: changePassword.fulfilled.type,
        payload: { message: 'Success' },
      });
      expect(state.loading).toBe(false);
      expect(state.error).toBe(null);
      expect(state.success).toBe(true);
    });

    it('should reset error and success when starting new operations', () => {
      const stateWithError: UserProfileState = {
        loading: false,
        error: 'Previous error',
        success: true,
      };

      const result = userProfileReducer(stateWithError, { type: updateUserProfile.pending.type });

      expect(result).toEqual({
        loading: true,
        error: null,
        success: false,
      });
    });
  });

  describe('console logging', () => {
    it('should log validation errors in updateUserProfile', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const validationError = new ValidationError('Validation failed');
      (apiClient.put as any).mockRejectedValue(validationError);
      (formatValidationError as any).mockReturnValue('Validation failed');

      await store.dispatch(updateUserProfile({ first_name: 'John' }));

      expect(consoleSpy).toHaveBeenCalledWith(
        'Validation error in updateUserProfile:',
        'Validation failed'
      );

      consoleSpy.mockRestore();
    });

    it('should log validation errors in updateNotificationPreferences', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const validationError = new ValidationError('Invalid preferences');
      (apiClient.put as any).mockRejectedValue(validationError);
      (formatValidationError as any).mockReturnValue('Invalid preferences');

      await store.dispatch(updateNotificationPreferences({ email_notifications: true }));

      expect(consoleSpy).toHaveBeenCalledWith(
        'Validation error in updateNotificationPreferences:',
        'Invalid preferences'
      );

      consoleSpy.mockRestore();
    });

    it('should log validation errors in uploadProfilePicture', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const validationError = new ValidationError('Invalid file');
      (apiClient.post as any).mockRejectedValue(validationError);
      (formatValidationError as any).mockReturnValue('Invalid file');

      const formData = new FormData();
      await store.dispatch(uploadProfilePicture(formData));

      expect(consoleSpy).toHaveBeenCalledWith(
        'Validation error in uploadProfilePicture:',
        'Invalid file'
      );

      consoleSpy.mockRestore();
    });

    it('should log validation errors in deleteProfilePicture', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const validationError = new ValidationError('Delete failed');
      (apiClient.delete as any).mockRejectedValue(validationError);
      (formatValidationError as any).mockReturnValue('Delete failed');

      await store.dispatch(deleteProfilePicture());

      expect(consoleSpy).toHaveBeenCalledWith(
        'Validation error in deleteProfilePicture:',
        'Delete failed'
      );

      consoleSpy.mockRestore();
    });
  });
});
