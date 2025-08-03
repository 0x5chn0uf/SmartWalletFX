import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../theme';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import PasswordChangeForm from '../../../components/profile/PasswordChangeForm';
import userProfileSlice from '../../../store/slices/userProfileSlice';
import authSlice from '../../../store/authSlice';

// Mock the userProfileSlice actions
vi.mock('../../../store/slices/userProfileSlice', async importOriginal => {
  const actual = await importOriginal();
  const mockChangePassword = vi.fn(() => ({ type: 'userProfile/changePassword/pending' }));
  mockChangePassword.fulfilled = { type: 'userProfile/changePassword/fulfilled' };
  mockChangePassword.pending = { type: 'userProfile/changePassword/pending' };
  mockChangePassword.rejected = { type: 'userProfile/changePassword/rejected' };

  return {
    ...actual,
    changePassword: mockChangePassword,
  };
});

describe('PasswordChangeForm', () => {
  const theme = createAppTheme();
  let mockStore: any;

  const mockUser = {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    email_verified: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockStore = configureStore({
      reducer: {
        auth: authSlice,
        userProfile: userProfileSlice,
      },
      preloadedState: {
        auth: {
          user: mockUser,
          isAuthenticated: true,
          token: 'mock-token',
          loading: false,
          error: null,
        },
        userProfile: {
          loading: false,
          error: null,
          success: false,
        },
      },
    });
  });

  const renderComponent = (customStore = mockStore) => {
    return render(
      <Provider store={customStore}>
        <ThemeProvider theme={theme}>
          <PasswordChangeForm />
        </ThemeProvider>
      </Provider>
    );
  };

  describe('Rendering', () => {
    it('renders all form fields', () => {
      renderComponent();

      const passwordInputs = screen.getAllByDisplayValue('');
      expect(passwordInputs).toHaveLength(3);
      expect(screen.getByText('Current Password')).toBeInTheDocument();
      expect(screen.getByText('New Password')).toBeInTheDocument();
      expect(screen.getByText('Confirm New Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /change password/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument();
    });

    it('shows password requirements alert', () => {
      renderComponent();

      expect(screen.getByText(/password requirements/i)).toBeInTheDocument();
      expect(screen.getByText(/at least 8 characters long/i)).toBeInTheDocument();
      expect(screen.getByText(/include uppercase and lowercase letters/i)).toBeInTheDocument();
    });

    it('shows login message when user is not authenticated', () => {
      const storeWithoutUser = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: null,
            isAuthenticated: false,
            token: null,
            loading: false,
            error: null,
          },
          userProfile: {
            loading: false,
            error: null,
            success: false,
          },
        },
      });

      renderComponent(storeWithoutUser);

      expect(screen.getByText(/please log in to change your password/i)).toBeInTheDocument();
    });
  });

  describe('Password Visibility Toggle', () => {
    it('toggles current password visibility', () => {
      renderComponent();

      const currentPasswordField = screen.getAllByDisplayValue('')[0] as HTMLInputElement;
      const toggleButton = screen.getAllByLabelText(/toggle.*password visibility/i)[0];

      expect(currentPasswordField.type).toBe('password');

      fireEvent.click(toggleButton);
      expect(currentPasswordField.type).toBe('text');

      fireEvent.click(toggleButton);
      expect(currentPasswordField.type).toBe('password');
    });

    it('toggles new password visibility', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1] as HTMLInputElement;
      const toggleButton = screen.getAllByLabelText(/toggle.*password visibility/i)[1];

      expect(newPasswordField.type).toBe('password');

      fireEvent.click(toggleButton);
      expect(newPasswordField.type).toBe('text');
    });

    it('toggles confirm password visibility', () => {
      renderComponent();

      const confirmPasswordField = screen.getAllByDisplayValue('')[2] as HTMLInputElement;
      const toggleButton = screen.getAllByLabelText(/toggle.*password visibility/i)[2];

      expect(confirmPasswordField.type).toBe('password');

      fireEvent.click(toggleButton);
      expect(confirmPasswordField.type).toBe('text');
    });
  });

  describe('Password Strength Indicator', () => {
    it('shows password strength when new password is entered', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1];

      fireEvent.change(newPasswordField, { target: { value: 'weak' } });

      expect(screen.getByText(/Strength: Weak/i)).toBeInTheDocument();
    });

    it('updates strength label based on password complexity', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1];

      // Weak password
      fireEvent.change(newPasswordField, { target: { value: 'weak' } });
      expect(screen.getByText(/Strength: Weak/i)).toBeInTheDocument();

      // Strong password
      fireEvent.change(newPasswordField, { target: { value: 'StrongPassword123!' } });
      expect(screen.getByText(/Strength: Very Strong/i)).toBeInTheDocument();
    });

    it('shows feedback suggestions for password improvement', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1];

      fireEvent.change(newPasswordField, { target: { value: 'weak' } });

      expect(screen.getByText(/suggestions:/i)).toBeInTheDocument();
      expect(screen.getByText(/suggestions:.*at least 8 characters/i)).toBeInTheDocument();
    });

    it('hides strength indicator when password field is empty', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1];

      fireEvent.change(newPasswordField, { target: { value: 'test' } });
      expect(screen.getByText(/Strength:/i)).toBeInTheDocument();

      fireEvent.change(newPasswordField, { target: { value: '' } });
      expect(screen.queryByText(/Strength:/i)).not.toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows validation error for empty current password', async () => {
      renderComponent();

      // Find the form element directly and trigger submit
      const forms = document.querySelectorAll('form');
      const form = forms[0];
      expect(form).toBeTruthy();

      fireEvent.submit(form);

      await waitFor(
        () => {
          // Check if there's any helper text showing validation error
          const helperText = screen.queryByText(/Current password is required/i);
          expect(helperText).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('shows validation error for short new password', async () => {
      renderComponent();

      const passwordInputs = screen.getAllByDisplayValue('');
      const currentPasswordField = passwordInputs[0];
      const newPasswordField = passwordInputs[1];
      const confirmPasswordField = passwordInputs[2];

      fireEvent.change(currentPasswordField, { target: { value: 'current123' } });
      fireEvent.change(newPasswordField, { target: { value: 'short' } });
      fireEvent.change(confirmPasswordField, { target: { value: 'short' } });

      // Find the form element directly and trigger submit
      const forms = document.querySelectorAll('form');
      const form = forms[0];
      expect(form).toBeTruthy();

      fireEvent.submit(form);

      await waitFor(
        () => {
          expect(screen.getByText(/Password must be at least 8 characters/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('shows validation error for mismatched passwords', async () => {
      renderComponent();

      const passwordInputs = screen.getAllByDisplayValue('');
      const currentPasswordField = passwordInputs[0];
      const newPasswordField = passwordInputs[1];
      const confirmPasswordField = passwordInputs[2];

      fireEvent.change(currentPasswordField, { target: { value: 'current123' } });
      fireEvent.change(newPasswordField, { target: { value: 'NewPassword123!' } });
      fireEvent.change(confirmPasswordField, { target: { value: 'DifferentPassword123!' } });

      // Find the form element directly and trigger submit
      const forms = document.querySelectorAll('form');
      const form = forms[0];
      expect(form).toBeTruthy();

      fireEvent.submit(form);

      await waitFor(
        () => {
          expect(screen.getByText(/Passwords don't match/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('clears validation errors when user starts typing', async () => {
      renderComponent();

      const passwordInputs = screen.getAllByDisplayValue('');
      const currentPasswordField = passwordInputs[0];

      // Find the form element directly and trigger submit
      const forms = document.querySelectorAll('form');
      const form = forms[0];
      expect(form).toBeTruthy();

      // Trigger validation error
      fireEvent.submit(form);

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText(/Current password is required/i)).toBeInTheDocument();
      });

      // Start typing to clear error
      fireEvent.change(currentPasswordField, { target: { value: 'c' } });

      await waitFor(() => {
        expect(screen.queryByText(/Current password is required/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      const mockDispatch = vi
        .fn()
        .mockImplementation(() => Promise.resolve({ unwrap: () => Promise.resolve() }));
      mockStore.dispatch = mockDispatch;

      renderComponent();

      const passwordInputs = screen.getAllByDisplayValue('');
      const currentPasswordField = passwordInputs[0];
      const newPasswordField = passwordInputs[1];
      const confirmPasswordField = passwordInputs[2];
      const submitButton = screen.getByRole('button', { name: /change password/i });

      fireEvent.change(currentPasswordField, { target: { value: 'currentPassword123' } });
      fireEvent.change(newPasswordField, { target: { value: 'NewPassword123!' } });
      fireEvent.change(confirmPasswordField, { target: { value: 'NewPassword123!' } });

      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalled();
      });
    });

    it('disables submit button when password strength is weak', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1];
      const submitButton = screen.getByRole('button', { name: /change password/i });

      fireEvent.change(newPasswordField, { target: { value: 'weak' } });

      expect(submitButton).toBeDisabled();
    });

    it('enables submit button when password strength is adequate', () => {
      renderComponent();

      const passwordInputs = screen.getAllByDisplayValue('');
      const currentPasswordField = passwordInputs[0];
      const newPasswordField = passwordInputs[1];
      const confirmPasswordField = passwordInputs[2];
      const submitButton = screen.getByRole('button', { name: /change password/i });

      fireEvent.change(currentPasswordField, { target: { value: 'current123' } });
      fireEvent.change(newPasswordField, { target: { value: 'StrongPassword123!' } });
      fireEvent.change(confirmPasswordField, { target: { value: 'StrongPassword123!' } });

      expect(submitButton).not.toBeDisabled();
    });

    it('prevents form submission when validation fails', async () => {
      const mockDispatch = vi
        .fn()
        .mockImplementation(() => Promise.resolve({ unwrap: () => Promise.resolve() }));
      mockStore.dispatch = mockDispatch;

      renderComponent();

      const submitButton = screen.getByRole('button', { name: /change password/i });

      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockDispatch).not.toHaveBeenCalled();
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading state during form submission', () => {
      const storeWithLoading = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: mockUser,
            isAuthenticated: true,
            token: 'mock-token',
            loading: false,
            error: null,
          },
          userProfile: {
            loading: true,
            error: null,
            success: false,
          },
        },
      });

      renderComponent(storeWithLoading);

      expect(screen.getByText(/changing password.../i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /changing password.../i })).toBeDisabled();
    });

    it('disables form fields during loading', () => {
      const storeWithLoading = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: mockUser,
            isAuthenticated: true,
            token: 'mock-token',
            loading: false,
            error: null,
          },
          userProfile: {
            loading: true,
            error: null,
            success: false,
          },
        },
      });

      renderComponent(storeWithLoading);

      const passwordInputs = screen.getAllByDisplayValue('');
      expect(passwordInputs[0]).toBeDisabled();
      expect(passwordInputs[1]).toBeDisabled();
      expect(passwordInputs[2]).toBeDisabled();
    });
  });

  describe('Error and Success States', () => {
    it('displays error message when password change fails', () => {
      const storeWithError = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: mockUser,
            isAuthenticated: true,
            token: 'mock-token',
            loading: false,
            error: null,
          },
          userProfile: {
            loading: false,
            error: 'Current password is incorrect',
            success: false,
          },
        },
      });

      renderComponent(storeWithError);

      expect(screen.getByText(/current password is incorrect/i)).toBeInTheDocument();
    });

    it('displays success message when password change succeeds', () => {
      const storeWithSuccess = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: mockUser,
            isAuthenticated: true,
            token: 'mock-token',
            loading: false,
            error: null,
          },
          userProfile: {
            loading: false,
            error: null,
            success: true,
          },
        },
      });

      renderComponent(storeWithSuccess);

      expect(screen.getByText(/password changed successfully!/i)).toBeInTheDocument();
    });
  });

  describe('Clear Functionality', () => {
    it('clears all form fields when clear button is clicked', () => {
      renderComponent();

      const currentPasswordField = screen.getAllByDisplayValue('')[0] as HTMLInputElement;
      const newPasswordField = screen.getAllByDisplayValue('')[1] as HTMLInputElement;
      const confirmPasswordField = screen.getAllByDisplayValue('')[2] as HTMLInputElement;
      const clearButton = screen.getByRole('button', { name: /clear/i });

      // Fill form fields
      fireEvent.change(currentPasswordField, { target: { value: 'current123' } });
      fireEvent.change(newPasswordField, { target: { value: 'NewPassword123!' } });
      fireEvent.change(confirmPasswordField, { target: { value: 'NewPassword123!' } });

      expect(currentPasswordField.value).toBe('current123');
      expect(newPasswordField.value).toBe('NewPassword123!');
      expect(confirmPasswordField.value).toBe('NewPassword123!');

      // Clear form
      fireEvent.click(clearButton);

      expect(currentPasswordField.value).toBe('');
      expect(newPasswordField.value).toBe('');
      expect(confirmPasswordField.value).toBe('');
    });

    it('clears password strength indicator when clear button is clicked', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1];
      const clearButton = screen.getByRole('button', { name: /clear/i });

      // Enter password to show strength indicator
      fireEvent.change(newPasswordField, { target: { value: 'TestPassword123!' } });
      expect(screen.getByText(/Strength:/i)).toBeInTheDocument();

      // Clear form
      fireEvent.click(clearButton);
      expect(screen.queryByText(/Strength:/i)).not.toBeInTheDocument();
    });

    it('disables clear button during loading', () => {
      const storeWithLoading = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: mockUser,
            isAuthenticated: true,
            token: 'mock-token',
            loading: false,
            error: null,
          },
          userProfile: {
            loading: true,
            error: null,
            success: false,
          },
        },
      });

      renderComponent(storeWithLoading);

      expect(screen.getByRole('button', { name: /clear/i })).toBeDisabled();
    });
  });

  describe('Password Strength Calculation', () => {
    it('calculates weak password strength correctly', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1];

      fireEvent.change(newPasswordField, { target: { value: 'weak' } });

      expect(screen.getByText(/Strength: Weak/i)).toBeInTheDocument();
    });

    it('calculates medium password strength correctly', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1];

      fireEvent.change(newPasswordField, { target: { value: 'Medium123' } });

      expect(screen.getByText(/Strength: Medium/i)).toBeInTheDocument();
    });

    it('calculates strong password strength correctly', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1];

      fireEvent.change(newPasswordField, { target: { value: 'StrongPass123!' } });

      expect(screen.getByText(/strength.*strong/i)).toBeInTheDocument();
    });

    it('calculates very strong password strength correctly', () => {
      renderComponent();

      const newPasswordField = screen.getAllByDisplayValue('')[1];

      fireEvent.change(newPasswordField, { target: { value: 'VeryStrongPassword123!' } });

      expect(screen.getByText(/Strength: Very Strong/i)).toBeInTheDocument();
    });
  });
});
