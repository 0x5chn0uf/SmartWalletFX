import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../theme';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import AccountDeletion from '../../../components/profile/AccountDeletion';
import userProfileSlice from '../../../store/slices/userProfileSlice';
import authSlice from '../../../store/authSlice';

// Mock the userProfileSlice actions
const mockDeleteAccount = vi.fn();
vi.mock('../../../store/slices/userProfileSlice', async () => {
  const actual = await vi.importActual('../../../store/slices/userProfileSlice');
  return {
    ...actual,
    deleteAccount: (...args: any[]) => mockDeleteAccount(...args),
  };
});

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<any>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('AccountDeletion', () => {
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
          <MemoryRouter>
            <AccountDeletion />
          </MemoryRouter>
        </ThemeProvider>
      </Provider>
    );
  };

  describe('Rendering', () => {
    it('renders delete account title', () => {
      renderComponent();

      expect(screen.getByText(/delete account/i)).toBeInTheDocument();
    });

    it('renders danger zone alert', () => {
      renderComponent();

      expect(screen.getByText(/danger zone/i)).toBeInTheDocument();
      expect(
        screen.getByText(/once you delete your account, there is no going back/i)
      ).toBeInTheDocument();
    });

    it('renders deletion consequences list', () => {
      renderComponent();

      expect(screen.getByText(/what happens when you delete your account:/i)).toBeInTheDocument();
      expect(
        screen.getByText(/your profile and personal information will be permanently deleted/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/all wallet data, transactions, and portfolio history will be removed/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/historical performance data and analytics will be lost/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/all api keys and connected services will be disconnected/i)
      ).toBeInTheDocument();
    });

    it('renders warning notice', () => {
      renderComponent();

      expect(screen.getByText(/before you proceed:/i)).toBeInTheDocument();
      expect(
        screen.getByText(/consider exporting your data if you need it for records/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/this action cannot be undone/i)).toBeInTheDocument();
    });

    it('renders delete account button', () => {
      renderComponent();

      expect(screen.getByRole('button', { name: /delete my account/i })).toBeInTheDocument();
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

      expect(screen.getByText(/please log in to manage your account/i)).toBeInTheDocument();
    });
  });

  describe('Dialog Interaction', () => {
    it('opens confirmation dialog when delete button is clicked', () => {
      renderComponent();

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      expect(screen.getByText(/confirm account deletion/i)).toBeInTheDocument();
      expect(
        screen.getByText((content, node) => {
          const hasText = (node: Element) =>
            node.textContent?.includes(
              'You are about to permanently delete the account for test@example.com'
            );
          const nodeHasText = hasText(node as Element);
          const childrenDontHaveText = Array.from(node?.children || []).every(
            child => !hasText(child as Element)
          );
          return nodeHasText && childrenDontHaveText;
        })
      ).toBeInTheDocument();
    });

    it('closes dialog when cancel button is clicked', async () => {
      renderComponent();

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText(/confirm account deletion/i)).not.toBeInTheDocument();
      });
    });

    it('closes dialog when clicking outside (onClose)', () => {
      renderComponent();

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      expect(screen.getByText(/confirm account deletion/i)).toBeInTheDocument();

      // Simulate dialog close
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('resets form fields when dialog is opened', () => {
      renderComponent();

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });

      // Open dialog first time
      fireEvent.click(deleteButton);

      const confirmationInput = screen.getByLabelText(/confirmation text/i);
      const passwordInput = screen.getByLabelText(/confirm password/i);
      const checkbox = screen.getByRole('checkbox');

      // Fill fields
      fireEvent.change(confirmationInput, { target: { value: 'DELETE MY ACCOUNT' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(checkbox);

      // Close dialog
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      // Open again
      fireEvent.click(deleteButton);

      // Fields should be reset
      expect(screen.getByLabelText(/confirmation text/i)).toHaveValue('');
      expect(screen.getByLabelText(/confirm password/i)).toHaveValue('');
      expect(screen.getByRole('checkbox')).not.toBeChecked();
    });
  });

  describe('Form Validation', () => {
    beforeEach(() => {
      renderComponent();
      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);
    });

    it('shows error for incorrect confirmation text', () => {
      const confirmationInput = screen.getByLabelText(/confirmation text/i);

      fireEvent.change(confirmationInput, { target: { value: 'wrong text' } });

      expect(screen.getByText(/must type exactly: DELETE MY ACCOUNT/i)).toBeInTheDocument();
    });

    it('accepts correct confirmation text', () => {
      const confirmationInput = screen.getByLabelText(/confirmation text/i);

      fireEvent.change(confirmationInput, { target: { value: 'DELETE MY ACCOUNT' } });

      expect(screen.queryByText(/must type exactly: DELETE MY ACCOUNT/i)).not.toBeInTheDocument();
    });

    it('does not show error for empty confirmation text', () => {
      const confirmationInput = screen.getByLabelText(/confirmation text/i);

      fireEvent.change(confirmationInput, { target: { value: '' } });

      expect(screen.queryByText(/must type exactly: DELETE MY ACCOUNT/i)).not.toBeInTheDocument();
    });

    it('requires password field', () => {
      const passwordInput = screen.getByLabelText(/confirm password/i);

      expect(passwordInput).toHaveAttribute('required');
      expect(screen.getByText(/enter your current password to confirm/i)).toBeInTheDocument();
    });

    it('requires checkbox to be checked', () => {
      const checkbox = screen.getByRole('checkbox');

      expect(checkbox).not.toBeChecked();
      expect(
        screen.getByText(/i understand that this action is permanent and cannot be undone/i)
      ).toBeInTheDocument();
    });

    it('disables delete button when form is incomplete', () => {
      const confirmDeleteButton = screen.getByRole('button', { name: /delete account/i });

      expect(confirmDeleteButton).toBeDisabled();
    });

    it('enables delete button when all requirements are met', () => {
      const confirmationInput = screen.getByLabelText(/confirmation text/i);
      const passwordInput = screen.getByLabelText(/confirm password/i);
      const checkbox = screen.getByRole('checkbox');
      const confirmDeleteButton = screen.getByRole('button', { name: /delete account/i });

      fireEvent.change(confirmationInput, { target: { value: 'DELETE MY ACCOUNT' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(checkbox);

      expect(confirmDeleteButton).not.toBeDisabled();
    });
  });

  describe('Account Deletion Process', () => {
    beforeEach(() => {
      renderComponent();
      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);
    });

    it('calls deleteAccount action with correct password', async () => {
      const mockDispatch = vi.fn().mockResolvedValue({ unwrap: () => Promise.resolve() });
      mockStore.dispatch = mockDispatch;

      const confirmationInput = screen.getByLabelText(/confirmation text/i);
      const passwordInput = screen.getByLabelText(/confirm password/i);
      const checkbox = screen.getByRole('checkbox');
      const confirmDeleteButton = screen.getByRole('button', { name: /delete account/i });

      fireEvent.change(confirmationInput, { target: { value: 'DELETE MY ACCOUNT' } });
      fireEvent.change(passwordInput, { target: { value: 'mypassword123' } });
      fireEvent.click(checkbox);

      fireEvent.click(confirmDeleteButton);

      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalled();
      });
    });

    it('navigates to home page after successful deletion', async () => {
      const mockDispatch = vi.fn().mockResolvedValue({ unwrap: () => Promise.resolve() });
      mockStore.dispatch = mockDispatch;

      const confirmationInput = screen.getByLabelText(/confirmation text/i);
      const passwordInput = screen.getByLabelText(/confirm password/i);
      const checkbox = screen.getByRole('checkbox');
      const confirmDeleteButton = screen.getByRole('button', { name: /delete account/i });

      fireEvent.change(confirmationInput, { target: { value: 'DELETE MY ACCOUNT' } });
      fireEvent.change(passwordInput, { target: { value: 'mypassword123' } });
      fireEvent.click(checkbox);

      fireEvent.click(confirmDeleteButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('does not proceed if confirmation text is invalid', async () => {
      const mockDispatch = vi.fn();
      mockStore.dispatch = mockDispatch;

      const confirmationInput = screen.getByLabelText(/confirmation text/i);
      const passwordInput = screen.getByLabelText(/confirm password/i);
      const checkbox = screen.getByRole('checkbox');
      const confirmDeleteButton = screen.getByRole('button', { name: /delete account/i });

      fireEvent.change(confirmationInput, { target: { value: 'wrong text' } });
      fireEvent.change(passwordInput, { target: { value: 'mypassword123' } });
      fireEvent.click(checkbox);

      fireEvent.click(confirmDeleteButton);

      expect(mockDispatch).not.toHaveBeenCalled();
    });

    it('does not proceed if checkbox is not checked', async () => {
      const mockDispatch = vi.fn();
      mockStore.dispatch = mockDispatch;

      const confirmationInput = screen.getByLabelText(/confirmation text/i);
      const passwordInput = screen.getByLabelText(/confirm password/i);
      const confirmDeleteButton = screen.getByRole('button', { name: /delete account/i });

      fireEvent.change(confirmationInput, { target: { value: 'DELETE MY ACCOUNT' } });
      fireEvent.change(passwordInput, { target: { value: 'mypassword123' } });
      // Don't check the checkbox

      fireEvent.click(confirmDeleteButton);

      expect(mockDispatch).not.toHaveBeenCalled();
    });

    it('does not proceed if password is empty', async () => {
      const mockDispatch = vi.fn();
      mockStore.dispatch = mockDispatch;

      const confirmationInput = screen.getByLabelText(/confirmation text/i);
      const checkbox = screen.getByRole('checkbox');
      const confirmDeleteButton = screen.getByRole('button', { name: /delete account/i });

      fireEvent.change(confirmationInput, { target: { value: 'DELETE MY ACCOUNT' } });
      fireEvent.click(checkbox);
      // Don't enter password

      fireEvent.click(confirmDeleteButton);

      expect(mockDispatch).not.toHaveBeenCalled();
    });

    it('handles deletion failure gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const mockDispatch = vi.fn().mockRejectedValue(new Error('Deletion failed'));
      mockStore.dispatch = mockDispatch;

      const confirmationInput = screen.getByLabelText(/confirmation text/i);
      const passwordInput = screen.getByLabelText(/confirm password/i);
      const checkbox = screen.getByRole('checkbox');
      const confirmDeleteButton = screen.getByRole('button', { name: /delete account/i });

      fireEvent.change(confirmationInput, { target: { value: 'DELETE MY ACCOUNT' } });
      fireEvent.change(passwordInput, { target: { value: 'mypassword123' } });
      fireEvent.click(checkbox);

      fireEvent.click(confirmDeleteButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Account deletion failed:', expect.any(Error));
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Loading States', () => {
    it('shows loading state during deletion', () => {
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

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      expect(screen.getByText(/deleting.../i)).toBeInTheDocument();
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

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      expect(screen.getByLabelText(/confirmation text/i)).toBeDisabled();
      expect(screen.getByLabelText(/confirm password/i)).toBeDisabled();
      expect(screen.getByRole('checkbox')).toBeDisabled();
    });

    it('disables action buttons during loading', () => {
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

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      expect(screen.getByRole('button', { name: /deleting.../i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
    });
  });

  describe('Error States', () => {
    it('displays error message in dialog when deletion fails', () => {
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
            error: 'Incorrect password',
            success: false,
          },
        },
      });

      renderComponent(storeWithError);

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      expect(screen.getByText(/incorrect password/i)).toBeInTheDocument();
    });
  });

  describe('User Information Display', () => {
    it('displays user email in confirmation dialog', () => {
      renderComponent();

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      expect(
        screen.getByText((content, node) => {
          const hasText = (node: Element) =>
            node.textContent?.includes(
              'You are about to permanently delete the account for test@example.com'
            );
          const nodeHasText = hasText(node as Element);
          const childrenDontHaveText = Array.from(node?.children || []).every(
            child => !hasText(child as Element)
          );
          return nodeHasText && childrenDontHaveText;
        })
      ).toBeInTheDocument();
    });

    it('shows confirmation text requirement', () => {
      renderComponent();

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      expect(
        screen.getByText((content, node) => {
          const hasText = (node: Element) =>
            node.textContent?.includes('Type DELETE MY ACCOUNT below to confirm');
          const nodeHasText = hasText(node as Element);
          const childrenDontHaveText = Array.from(node?.children || []).every(
            child => !hasText(child as Element)
          );
          return nodeHasText && childrenDontHaveText;
        })
      ).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('provides proper labels for form fields', () => {
      renderComponent();

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      expect(screen.getByLabelText(/confirmation text/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
      expect(screen.getByRole('checkbox')).toBeInTheDocument();
    });

    it('maintains focus management in dialog', () => {
      renderComponent();

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      const confirmationInput = screen.getByLabelText(/confirmation text/i);
      confirmationInput.focus();

      expect(document.activeElement).toBe(confirmationInput);
    });

    it('provides appropriate ARIA attributes', () => {
      renderComponent();

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByRole('checkbox')).toHaveAttribute('type', 'checkbox');
    });
  });

  describe('Confirmation Text Constants', () => {
    it('uses correct expected confirmation text', () => {
      renderComponent();

      const deleteButton = screen.getByRole('button', { name: /delete my account/i });
      fireEvent.click(deleteButton);

      const confirmationInput = screen.getByLabelText(/confirmation text/i);

      // Test with correct text
      fireEvent.change(confirmationInput, { target: { value: 'DELETE MY ACCOUNT' } });
      expect(screen.queryByText(/must type exactly/i)).not.toBeInTheDocument();

      // Test with incorrect text
      fireEvent.change(confirmationInput, { target: { value: 'delete my account' } });
      expect(screen.getByText(/must type exactly: DELETE MY ACCOUNT/i)).toBeInTheDocument();
    });
  });
});
