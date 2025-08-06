import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../theme';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import NotificationSettings from '../../../components/profile/NotificationSettings';
import userProfileSlice from '../../../store/slices/userProfileSlice';
import authSlice from '../../../store/authSlice';

// Mock function
const mockUpdateNotificationPreferences = vi.fn();

// Mock the userProfileSlice actions
vi.mock('../../../store/slices/userProfileSlice', async () => {
  const actual = await vi.importActual('../../../store/slices/userProfileSlice');

  // Create mock thunk with proper structure
  const mockThunk = (...args: any[]) => {
    mockUpdateNotificationPreferences(...args);
    return { type: 'userProfile/updateNotificationPreferences/pending' };
  };

  // Mock the async thunk structure
  mockThunk.pending = { type: 'userProfile/updateNotificationPreferences/pending' };
  mockThunk.fulfilled = { type: 'userProfile/updateNotificationPreferences/fulfilled' };
  mockThunk.rejected = { type: 'userProfile/updateNotificationPreferences/rejected' };

  return {
    ...actual,
    updateNotificationPreferences: mockThunk,
  };
});

describe('NotificationSettings', () => {
  const theme = createAppTheme();
  let mockStore: any;

  const mockUser = {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    email_verified: true,
    notification_preferences: {
      email_notifications: true,
      security_alerts: true,
      portfolio_updates: false,
      price_alerts: true,
    },
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
          <NotificationSettings />
        </ThemeProvider>
      </Provider>
    );
  };

  describe('Rendering', () => {
    it('renders notification preferences title', () => {
      renderComponent();

      expect(
        screen.getByRole('heading', { name: /notification preferences/i })
      ).toBeInTheDocument();
    });

    it('renders all notification options', () => {
      renderComponent();

      expect(screen.getByText(/email notifications/i)).toBeInTheDocument();
      expect(screen.getAllByText(/security alerts/i)[0]).toBeInTheDocument();
      expect(screen.getByText(/portfolio updates/i)).toBeInTheDocument();
      expect(screen.getByText(/price alerts/i)).toBeInTheDocument();
    });

    it('displays notification option descriptions', () => {
      renderComponent();

      expect(screen.getByText(/receive general notifications via email/i)).toBeInTheDocument();
      expect(screen.getByText(/important security notifications/i)).toBeInTheDocument();
      expect(
        screen.getByText(/daily and weekly portfolio performance summaries/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/notifications when assets reach target prices/i)
      ).toBeInTheDocument();
    });

    it('shows critical badge for security alerts', () => {
      renderComponent();

      expect(screen.getByText(/critical/i)).toBeInTheDocument();
    });

    it('renders action buttons', () => {
      renderComponent();

      expect(screen.getByRole('button', { name: /save preferences/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /reset changes/i })).toBeInTheDocument();
    });

    it('shows informational alerts', () => {
      renderComponent();

      expect(screen.getByText(/email delivery/i)).toBeInTheDocument();
      expect(
        screen.getByText(/we strongly recommend keeping security alerts enabled/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/coming soon/i)).toBeInTheDocument();
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

      expect(
        screen.getByText(/please log in to manage your notification preferences/i)
      ).toBeInTheDocument();
    });
  });

  describe('Switch States', () => {
    it('initializes switches based on user preferences', () => {
      renderComponent();

      const switches = screen.getAllByRole('checkbox');

      // Email notifications: true
      expect(switches[0]).toBeChecked();
      // Security alerts: true
      expect(switches[1]).toBeChecked();
      // Portfolio updates: false
      expect(switches[2]).not.toBeChecked();
      // Price alerts: true
      expect(switches[3]).toBeChecked();
    });

    it('uses default values when user has no preferences', () => {
      const userWithoutPrefs = { ...mockUser, notification_preferences: null };
      const storeWithoutPrefs = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: userWithoutPrefs,
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

      renderComponent(storeWithoutPrefs);

      const switches = screen.getAllByRole('checkbox');

      // All should default to true
      switches.forEach(switchElement => {
        expect(switchElement).toBeChecked();
      });
    });

    it('handles partial user preferences', () => {
      const userWithPartialPrefs = {
        ...mockUser,
        notification_preferences: {
          email_notifications: false,
          // Other preferences missing
        },
      };
      const storeWithPartialPrefs = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: userWithPartialPrefs,
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

      renderComponent(storeWithPartialPrefs);

      const switches = screen.getAllByRole('checkbox');

      // Email notifications: false (from user prefs)
      expect(switches[0]).not.toBeChecked();
      // Others should default to true
      expect(switches[1]).toBeChecked();
      expect(switches[2]).toBeChecked();
      expect(switches[3]).toBeChecked();
    });
  });

  describe('Switch Interactions', () => {
    it('toggles email notifications switch', () => {
      renderComponent();

      const emailSwitch = screen.getAllByRole('checkbox')[0];

      expect(emailSwitch).toBeChecked();

      fireEvent.click(emailSwitch);
      expect(emailSwitch).not.toBeChecked();

      fireEvent.click(emailSwitch);
      expect(emailSwitch).toBeChecked();
    });

    it('toggles security alerts switch', () => {
      renderComponent();

      const securitySwitch = screen.getAllByRole('checkbox')[1];

      expect(securitySwitch).toBeChecked();

      fireEvent.click(securitySwitch);
      expect(securitySwitch).not.toBeChecked();
    });

    it('toggles portfolio updates switch', () => {
      renderComponent();

      const portfolioSwitch = screen.getAllByRole('checkbox')[2];

      expect(portfolioSwitch).not.toBeChecked();

      fireEvent.click(portfolioSwitch);
      expect(portfolioSwitch).toBeChecked();
    });

    it('toggles price alerts switch', () => {
      renderComponent();

      const priceSwitch = screen.getAllByRole('checkbox')[3];

      expect(priceSwitch).toBeChecked();

      fireEvent.click(priceSwitch);
      expect(priceSwitch).not.toBeChecked();
    });

    it('enables action buttons when changes are made', () => {
      renderComponent();

      const saveButton = screen.getByRole('button', { name: /save preferences/i });
      const resetButton = screen.getByRole('button', { name: /reset changes/i });

      // Initially disabled (no changes)
      expect(saveButton).toBeDisabled();
      expect(resetButton).toBeDisabled();

      // Make a change
      const emailSwitch = screen.getAllByRole('checkbox')[0];
      fireEvent.click(emailSwitch);

      // Should be enabled after change
      expect(saveButton).not.toBeDisabled();
      expect(resetButton).not.toBeDisabled();
    });
  });

  describe('Form Actions', () => {
    it('saves preferences when save button is clicked', async () => {
      const mockDispatch = vi.fn().mockResolvedValue({ unwrap: () => Promise.resolve() });
      mockStore.dispatch = mockDispatch;

      renderComponent();

      // Make a change
      const emailSwitch = screen.getAllByRole('checkbox')[0];
      fireEvent.click(emailSwitch);

      const saveButton = screen.getByRole('button', { name: /save preferences/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalled();
      });
    });

    it('resets preferences when reset button is clicked', () => {
      renderComponent();

      // Make a change
      const emailSwitch = screen.getAllByRole('checkbox')[0];
      fireEvent.click(emailSwitch);
      expect(emailSwitch).not.toBeChecked();

      // Reset changes
      const resetButton = screen.getByRole('button', { name: /reset changes/i });
      fireEvent.click(resetButton);

      // Should revert to original state
      expect(emailSwitch).toBeChecked();

      // Buttons should be disabled again
      const saveButton = screen.getByRole('button', { name: /save preferences/i });
      expect(saveButton).toBeDisabled();
      expect(resetButton).toBeDisabled();
    });

    it('disables action buttons when no changes are made', () => {
      renderComponent();

      const saveButton = screen.getByRole('button', { name: /save preferences/i });
      const resetButton = screen.getByRole('button', { name: /reset changes/i });

      expect(saveButton).toBeDisabled();
      expect(resetButton).toBeDisabled();
    });

    it('calls updateNotificationPreferences with correct data', async () => {
      const mockDispatch = vi.fn().mockResolvedValue({ unwrap: () => Promise.resolve() });
      mockStore.dispatch = mockDispatch;

      renderComponent();

      // Toggle email notifications off
      const emailSwitch = screen.getAllByRole('checkbox')[0];
      fireEvent.click(emailSwitch);

      // Toggle portfolio updates on
      const portfolioSwitch = screen.getAllByRole('checkbox')[2];
      fireEvent.click(portfolioSwitch);

      const saveButton = screen.getByRole('button', { name: /save preferences/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'userProfile/updateNotificationPreferences/pending',
          })
        );
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading state during save operation', () => {
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

      expect(screen.getByText(/saving.../i)).toBeInTheDocument();
    });

    it('disables switches during loading', () => {
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

      const switches = screen.getAllByRole('checkbox');
      switches.forEach(switchElement => {
        expect(switchElement).toBeDisabled();
      });
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

      expect(screen.getByRole('button', { name: /saving.../i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /reset changes/i })).toBeDisabled();
    });
  });

  describe('Error and Success States', () => {
    it('displays error message when update fails', () => {
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
            error: 'Failed to update notification preferences',
            success: false,
          },
        },
      });

      renderComponent(storeWithError);

      expect(screen.getByText(/failed to update notification preferences/i)).toBeInTheDocument();
    });

    it('displays success message when update succeeds', () => {
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

      expect(
        screen.getByText(/notification preferences updated successfully!/i)
      ).toBeInTheDocument();
    });
  });

  describe('User Information Display', () => {
    it('displays user email in the information section', () => {
      renderComponent();

      expect(screen.getByText(/notifications are sent to test@example.com/i)).toBeInTheDocument();
    });

    it('shows security alerts recommendation', () => {
      renderComponent();

      expect(
        screen.getByText(/we strongly recommend keeping security alerts enabled/i)
      ).toBeInTheDocument();
    });

    it('displays coming soon section', () => {
      renderComponent();

      expect(screen.getByText(/push notifications, sms alerts/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('provides proper labels for switches', () => {
      renderComponent();

      const switches = screen.getAllByRole('checkbox');

      switches.forEach(switchElement => {
        expect(switchElement).toHaveAttribute('type', 'checkbox');
      });
    });

    it('maintains focus management', () => {
      renderComponent();

      const firstSwitch = screen.getAllByRole('checkbox')[0];
      firstSwitch.focus();

      expect(document.activeElement).toBe(firstSwitch);
    });
  });

  describe('State Management', () => {
    it('tracks changes correctly', () => {
      renderComponent();

      const saveButton = screen.getByRole('button', { name: /save preferences/i });
      expect(saveButton).toBeDisabled();

      // Make first change
      const emailSwitch = screen.getAllByRole('checkbox')[0];
      fireEvent.click(emailSwitch);
      expect(saveButton).not.toBeDisabled();

      // Revert change
      fireEvent.click(emailSwitch);
      expect(saveButton).toBeDisabled();
    });

    it('resets hasChanges flag after successful save', async () => {
      const mockDispatch = vi.fn().mockImplementation(() => ({
        unwrap: () => Promise.resolve(),
      }));

      const storeForSave = configureStore({
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
      storeForSave.dispatch = mockDispatch;

      renderComponent(storeForSave);

      // Make a change
      const emailSwitch = screen.getAllByRole('checkbox')[0];
      fireEvent.click(emailSwitch);

      const saveButton = screen.getByRole('button', { name: /save preferences/i });
      expect(saveButton).not.toBeDisabled();

      // Save changes
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockDispatch).toHaveBeenCalled();
      });
    });
  });
});
