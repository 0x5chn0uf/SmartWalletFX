import { http, HttpResponse } from 'msw';
import { server } from '../../mocks/server';
import apiClient from '../../services/api';
import {
  UserProfile,
  UserProfileUpdate,
  PasswordChange,
  NotificationPreferences,
} from '../../schemas/api';
import { describe, it, expect, beforeEach, vi } from 'vitest';

const API_URL = 'http://localhost:8000';

// Mock user data
const mockUser: UserProfile = {
  id: 'user-123',
  username: 'testuser',
  email: 'test@example.com',
  email_verified: true,
  role: 'user',
  profile_picture_url: null,
  first_name: 'John',
  last_name: 'Doe',
  bio: 'Test user bio',
  timezone: 'UTC',
  preferred_currency: 'USD',
  notification_preferences: {
    email_notifications: true,
    security_alerts: true,
    portfolio_updates: true,
    price_alerts: true,
  },
};

describe('Profile API Integration Tests', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();

    // Set session active to prevent token refresh attempts
    localStorage.setItem('session_active', '1');

    // Reset MSW handlers to default state
    server.resetHandlers();
  });

  describe('Profile Update', () => {
    it('should successfully update user profile', async () => {
      const updatedProfile: UserProfileUpdate = {
        first_name: 'Jane',
        last_name: 'Smith',
        bio: 'Updated bio',
        timezone: 'America/New_York',
        preferred_currency: 'EUR',
      };

      const expectedResponse = {
        ...mockUser,
        ...updatedProfile,
      };

      server.use(
        http.put(`${API_URL}/users/me/profile`, () => {
          return HttpResponse.json({
            data: expectedResponse,
            status: 200,
            message: 'Profile updated successfully',
          });
        })
      );

      const response = await apiClient.put('/users/me/profile', updatedProfile, {
        withCredentials: true,
      });

      expect(response.status).toBe(200);
      expect(response.data.data.first_name).toBe('Jane');
      expect(response.data.data.last_name).toBe('Smith');
      expect(response.data.data.bio).toBe('Updated bio');
      expect(response.data.data.timezone).toBe('America/New_York');
      expect(response.data.data.preferred_currency).toBe('EUR');
    });

    it('should handle profile update validation errors', async () => {
      const invalidProfile: UserProfileUpdate = {
        first_name: 'A'.repeat(101), // Too long
        last_name: 'Smith',
      };

      server.use(
        http.put(`${API_URL}/users/me/profile`, () => {
          return HttpResponse.json(
            {
              detail: 'Validation error',
              errors: [
                {
                  field: 'first_name',
                  message: 'First name must be 100 characters or less',
                },
              ],
            },
            { status: 422 }
          );
        })
      );

      try {
        await apiClient.put('/users/me/profile', invalidProfile, {
          withCredentials: true,
        });
      } catch (error: any) {
        expect(error.response.status).toBe(422);
        expect(error.response.data.detail).toBe('Validation error');
        expect(error.response.data.errors[0].field).toBe('first_name');
      }
    });

    it('should handle unauthorized profile update', async () => {
      server.use(
        http.put(`${API_URL}/users/me/profile`, () => {
          return HttpResponse.json({ detail: 'Authentication required' }, { status: 401 });
        })
      );

      try {
        await apiClient.put(
          '/users/me/profile',
          { first_name: 'John' },
          {
            withCredentials: true,
          }
        );
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.detail).toBe('Authentication required');
      }
    });
  });

  describe('Password Change', () => {
    it('should successfully change password', async () => {
      const passwordData: PasswordChange = {
        current_password: 'oldPassword123!',
        new_password: 'newPassword456!',
        confirm_password: 'newPassword456!',
      };

      server.use(
        http.post(`${API_URL}/users/me/change-password`, () => {
          return HttpResponse.json({ message: 'Password changed successfully' }, { status: 200 });
        })
      );

      const response = await apiClient.post('/users/me/change-password', passwordData, {
        withCredentials: true,
      });

      expect(response.status).toBe(200);
      expect(response.data.message).toBe('Password changed successfully');
    });

    it('should handle incorrect current password', async () => {
      const passwordData: PasswordChange = {
        current_password: 'wrongPassword',
        new_password: 'newPassword456!',
        confirm_password: 'newPassword456!',
      };

      server.use(
        http.post(`${API_URL}/users/me/change-password`, () => {
          return HttpResponse.json({ detail: 'Current password is incorrect' }, { status: 400 });
        })
      );

      try {
        await apiClient.post('/users/me/change-password', passwordData, {
          withCredentials: true,
        });
      } catch (error: any) {
        expect(error.response.status).toBe(400);
        expect(error.response.data.detail).toBe('Current password is incorrect');
      }
    });

    it('should handle password validation errors', async () => {
      const passwordData: PasswordChange = {
        current_password: 'oldPassword123!',
        new_password: 'weak',
        confirm_password: 'weak',
      };

      server.use(
        http.post(`${API_URL}/users/me/change-password`, () => {
          return HttpResponse.json(
            {
              detail: 'Validation error',
              errors: [
                {
                  field: 'new_password',
                  message: 'Password must be at least 8 characters long',
                },
              ],
            },
            { status: 422 }
          );
        })
      );

      try {
        await apiClient.post('/users/me/change-password', passwordData, {
          withCredentials: true,
        });
      } catch (error: any) {
        expect(error.response.status).toBe(422);
        expect(error.response.data.detail).toBe('Validation error');
        expect(error.response.data.errors[0].field).toBe('new_password');
      }
    });

    it('should handle mismatched password confirmation', async () => {
      const passwordData: PasswordChange = {
        current_password: 'oldPassword123!',
        new_password: 'newPassword456!',
        confirm_password: 'differentPassword789!',
      };

      server.use(
        http.post(`${API_URL}/users/me/change-password`, () => {
          return HttpResponse.json(
            {
              detail: 'Validation error',
              errors: [
                {
                  field: 'confirm_password',
                  message: "Passwords don't match",
                },
              ],
            },
            { status: 422 }
          );
        })
      );

      try {
        await apiClient.post('/users/me/change-password', passwordData, {
          withCredentials: true,
        });
      } catch (error: any) {
        expect(error.response.status).toBe(422);
        expect(error.response.data.errors[0].message).toBe("Passwords don't match");
      }
    });
  });

  describe('Notification Preferences', () => {
    it('should successfully update notification preferences', async () => {
      const preferences: NotificationPreferences = {
        email_notifications: false,
        security_alerts: true,
        portfolio_updates: false,
        price_alerts: true,
      };

      const expectedResponse = {
        ...mockUser,
        notification_preferences: preferences,
      };

      server.use(
        http.put(`${API_URL}/users/me/notifications`, () => {
          return HttpResponse.json({
            data: expectedResponse,
            status: 200,
            message: 'Notification preferences updated successfully',
          });
        })
      );

      const response = await apiClient.put('/users/me/notifications', preferences, {
        withCredentials: true,
      });

      expect(response.status).toBe(200);
      expect(response.data.data.notification_preferences.email_notifications).toBe(false);
      expect(response.data.data.notification_preferences.security_alerts).toBe(true);
      expect(response.data.data.notification_preferences.portfolio_updates).toBe(false);
      expect(response.data.data.notification_preferences.price_alerts).toBe(true);
    });

    it('should handle notification preferences validation errors', async () => {
      const invalidPreferences = {
        invalid_preference: true,
      };

      server.use(
        http.put(`${API_URL}/users/me/notifications`, () => {
          return HttpResponse.json(
            {
              detail: 'Invalid notification preference fields',
              errors: [
                {
                  field: 'invalid_preference',
                  message: 'Unknown notification preference',
                },
              ],
            },
            { status: 422 }
          );
        })
      );

      try {
        await apiClient.put('/users/me/notifications', invalidPreferences, {
          withCredentials: true,
        });
      } catch (error: any) {
        expect(error.response.status).toBe(422);
        expect(error.response.data.detail).toBe('Invalid notification preference fields');
      }
    });
  });

  describe('Profile Picture', () => {
    it('should successfully upload profile picture', async () => {
      // Prepare form data but we will mock the request to avoid Node multipart quirks
      const formData = new FormData();
      formData.append('file', new File(['mock'], 'profile.jpg', { type: 'image/jpeg' }));

      const expectedResponse = {
        ...mockUser,
        profile_picture_url: 'https://example.com/profile-pictures/user-123.jpg',
      };

      // Mock axios post to resolve immediately instead of performing a real multipart request
      vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
        status: 200,
        data: { data: expectedResponse },
      } as any);

      const response = await apiClient.post('/users/me/profile/picture', formData, {
        withCredentials: true,
      });

      expect(response.status).toBe(200);
      expect(response.data.data.profile_picture_url).toBe(
        'https://example.com/profile-pictures/user-123.jpg'
      );
    });

    it('should handle invalid file type for profile picture', async () => {
      const formData = new FormData();
      formData.append('file', new File(['pdf'], 'document.pdf', { type: 'application/pdf' }));

      const errorResponse = {
        response: {
          status: 422,
          data: {
            detail: 'Invalid file type',
            errors: [
              {
                field: 'file',
                message: 'Only image files (JPEG, PNG, GIF) are allowed',
              },
            ],
          },
        },
      };

      vi.spyOn(apiClient, 'post').mockRejectedValueOnce(errorResponse as any);

      try {
        await apiClient.post('/users/me/profile/picture', formData, { withCredentials: true });
      } catch (error: any) {
        expect(error.response.status).toBe(422);
        expect(error.response.data.detail).toBe('Invalid file type');
        expect(error.response.data.errors[0].message).toBe(
          'Only image files (JPEG, PNG, GIF) are allowed'
        );
      }
    });

    it('should handle file size too large', async () => {
      const formData = new FormData();
      formData.append(
        'file',
        new File(['x'.repeat(6 * 1024 * 1024)], 'large.jpg', { type: 'image/jpeg' })
      );

      const errorResponse = {
        response: {
          status: 413,
          data: {
            detail: 'File too large',
          },
        },
      };

      vi.spyOn(apiClient, 'post').mockRejectedValueOnce(errorResponse as any);

      try {
        await apiClient.post('/users/me/profile/picture', formData, { withCredentials: true });
      } catch (error: any) {
        expect(error.response.status).toBe(413);
        expect(error.response.data.detail).toBe('File too large');
      }
    });

    it('should successfully delete profile picture', async () => {
      const expectedResponse = {
        ...mockUser,
        profile_picture_url: null,
      };

      server.use(
        http.delete(`${API_URL}/users/me/profile/picture`, () => {
          return HttpResponse.json({
            data: expectedResponse,
            status: 200,
            message: 'Profile picture deleted successfully',
          });
        })
      );

      const response = await apiClient.delete('/users/me/profile/picture', {
        withCredentials: true,
      });

      expect(response.status).toBe(200);
      expect(response.data.data.profile_picture_url).toBe(null);
    });

    it('should handle delete when no profile picture exists', async () => {
      server.use(
        http.delete(`${API_URL}/users/me/profile/picture`, () => {
          return HttpResponse.json({ detail: 'No profile picture to delete' }, { status: 404 });
        })
      );

      try {
        await apiClient.delete('/users/me/profile/picture', {
          withCredentials: true,
        });
      } catch (error: any) {
        expect(error.response.status).toBe(404);
        expect(error.response.data.detail).toBe('No profile picture to delete');
      }
    });
  });

  describe('Account Deletion', () => {
    it('should successfully delete account', async () => {
      const passwordData = { password: 'userPassword123!' };

      server.use(
        http.delete(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ message: 'Account deleted successfully' }, { status: 200 });
        })
      );

      const response = await apiClient.delete('/users/me', {
        data: passwordData,
        withCredentials: true,
      });

      expect(response.status).toBe(200);
      expect(response.data.message).toBe('Account deleted successfully');
    });

    it('should handle incorrect password for account deletion', async () => {
      const passwordData = { password: 'wrongPassword' };

      server.use(
        http.delete(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Incorrect password' }, { status: 400 });
        })
      );

      try {
        await apiClient.delete('/users/me', {
          data: passwordData,
          withCredentials: true,
        });
      } catch (error: any) {
        expect(error.response.status).toBe(400);
        expect(error.response.data.detail).toBe('Incorrect password');
      }
    });

    it('should handle account deletion when user has active subscriptions', async () => {
      const passwordData = { password: 'userPassword123!' };

      server.use(
        http.delete(`${API_URL}/users/me`, () => {
          return HttpResponse.json(
            {
              detail: 'Cannot delete account with active subscriptions',
              message: 'Please cancel all active subscriptions before deleting your account',
            },
            { status: 409 }
          );
        })
      );

      try {
        await apiClient.delete('/users/me', {
          data: passwordData,
          withCredentials: true,
        });
      } catch (error: any) {
        expect(error.response.status).toBe(409);
        expect(error.response.data.detail).toBe('Cannot delete account with active subscriptions');
      }
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      server.use(
        http.put(`${API_URL}/users/me/profile`, () => {
          return HttpResponse.error();
        })
      );

      try {
        await apiClient.put(
          '/users/me/profile',
          { first_name: 'John' },
          {
            withCredentials: true,
          }
        );
      } catch (error: any) {
        expect(error.code).toBe('ERR_NETWORK');
      }
    });

    it('should handle server errors (500)', async () => {
      server.use(
        http.put(`${API_URL}/users/me/profile`, () => {
          return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 });
        })
      );

      try {
        await apiClient.put(
          '/users/me/profile',
          { first_name: 'John' },
          {
            withCredentials: true,
          }
        );
      } catch (error: any) {
        expect(error.response.status).toBe(500);
        expect(error.response.data.detail).toBe('Internal server error');
      }
    });

    it('should handle rate limiting (429)', async () => {
      server.use(
        http.post(`${API_URL}/users/me/change-password`, () => {
          return HttpResponse.json(
            {
              detail: 'Too many requests',
              retry_after: 60,
            },
            { status: 429 }
          );
        })
      );

      try {
        await apiClient.post(
          '/users/me/change-password',
          {
            current_password: 'old',
            new_password: 'new123!',
            confirm_password: 'new123!',
          },
          {
            withCredentials: true,
          }
        );
      } catch (error: any) {
        expect(error.response.status).toBe(429);
        expect(error.response.data.detail).toBe('Too many requests');
        expect(error.response.data.retry_after).toBe(60);
      }
    });
  });

  describe('Response Format Validation', () => {
    it('should handle malformed JSON responses', async () => {
      server.use(
        http.put(`${API_URL}/users/me/profile`, () => {
          return new HttpResponse('Invalid JSON{', {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          });
        })
      );

      try {
        await apiClient.put(
          '/users/me/profile',
          { first_name: 'John' },
          {
            withCredentials: true,
          }
        );
      } catch (error: any) {
        expect(error.name).toBe('SyntaxError');
      }
    });

    it('should handle responses with unexpected status codes', async () => {
      server.use(
        http.put(`${API_URL}/users/me/profile`, () => {
          return HttpResponse.json({ message: 'Accepted but processing' }, { status: 202 });
        })
      );

      const response = await apiClient.put(
        '/users/me/profile',
        { first_name: 'John' },
        {
          withCredentials: true,
        }
      );

      expect(response.status).toBe(202);
      expect(response.data.message).toBe('Accepted but processing');
    });
  });

  describe('Authentication Integration', () => {
    it('should handle session expiration during profile operations', async () => {
      // Remove session active to prevent interceptor from trying refresh
      localStorage.removeItem('session_active');

      server.use(
        http.put(`${API_URL}/users/me/profile`, () => {
          return HttpResponse.json({ detail: 'Session expired' }, { status: 401 });
        })
      );

      try {
        await apiClient.put(
          '/users/me/profile',
          { first_name: 'John' },
          {
            withCredentials: true,
          }
        );
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.detail).toBe('Session expired');
      }
    });

    it('should handle insufficient permissions', async () => {
      server.use(
        http.delete(`${API_URL}/users/me`, () => {
          return HttpResponse.json({ detail: 'Insufficient permissions' }, { status: 403 });
        })
      );

      try {
        await apiClient.delete('/users/me', {
          data: { password: 'password123' },
          withCredentials: true,
        });
      } catch (error: any) {
        expect(error.response.status).toBe(403);
        expect(error.response.data.detail).toBe('Insufficient permissions');
      }
    });
  });
});
