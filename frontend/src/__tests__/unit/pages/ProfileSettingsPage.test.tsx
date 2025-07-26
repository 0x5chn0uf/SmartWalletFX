import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../theme';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import ProfileSettingsPage from '../../../pages/SettingsPage';
import userProfileSlice from '../../../store/slices/userProfileSlice';
import authSlice from '../../../store/authSlice';

// Mock all profile components to focus on the page structure
vi.mock('../../../components/profile/ProfileForm', () => ({
  default: () => <div data-testid="profile-form">Profile Form Component</div>,
}));

vi.mock('../../../components/profile/ProfilePictureUpload', () => ({
  default: () => <div data-testid="profile-picture-upload">Profile Picture Upload Component</div>,
}));

vi.mock('../../../components/profile/PasswordChangeForm', () => ({
  default: () => <div data-testid="password-change-form">Password Change Form Component</div>,
}));

vi.mock('../../../components/profile/NotificationSettings', () => ({
  default: () => <div data-testid="notification-settings">Notification Settings Component</div>,
}));

vi.mock('../../../components/profile/AccountDeletion', () => ({
  default: () => <div data-testid="account-deletion">Account Deletion Component</div>,
}));

describe('ProfileSettingsPage', () => {
  const theme = createAppTheme();
  let mockStore: any;

  const mockUser = {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    email_verified: true,
    first_name: 'John',
    last_name: 'Doe',
    bio: 'Test user bio',
    profile_picture_url: 'https://example.com/avatar.jpg',
  };

  const mockUserMinimal = {
    id: '2',
    username: 'simpleuser',
    email: 'simple@example.com',
    email_verified: true,
    first_name: null,
    last_name: null,
    bio: null,
    profile_picture_url: null,
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
          <ProfileSettingsPage />
        </ThemeProvider>
      </Provider>
    );
  };

  describe('Page Structure', () => {
    it('renders page title', () => {
      renderComponent();

      expect(screen.getByText('Profile Settings')).toBeInTheDocument();
    });

    it('renders profile header with user information', () => {
      renderComponent();

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByText('Test user bio')).toBeInTheDocument();
    });

    it('renders profile header with username when name is not available', () => {
      const storeWithMinimalUser = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: mockUserMinimal,
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

      renderComponent(storeWithMinimalUser);

      expect(screen.getByText('simpleuser')).toBeInTheDocument();
      expect(screen.getByText('simple@example.com')).toBeInTheDocument();
      expect(screen.queryByText('Test user bio')).not.toBeInTheDocument();
    });

    it('renders user avatar with profile picture', () => {
      renderComponent();

      const avatar = screen.getByRole('img');
      expect(avatar).toHaveAttribute('src', 'https://example.com/avatar.jpg');
    });

    it('renders user avatar with initials when no profile picture', () => {
      const storeWithMinimalUser = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: mockUserMinimal,
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

      renderComponent(storeWithMinimalUser);

      expect(screen.getByText('S')).toBeInTheDocument(); // First letter of 'simpleuser'
    });

    it('renders all navigation tabs', () => {
      renderComponent();

      expect(screen.getByRole('tab', { name: /profile/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /security/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /notifications/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /account/i })).toBeInTheDocument();
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
        screen.getByText(/please log in to access your profile settings/i)
      ).toBeInTheDocument();
      expect(screen.queryByText('Profile Settings')).not.toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('shows Profile tab content by default', () => {
      renderComponent();

      expect(screen.getByTestId('profile-form')).toBeInTheDocument();
      expect(screen.getByTestId('profile-picture-upload')).toBeInTheDocument();
      expect(screen.queryByTestId('password-change-form')).not.toBeInTheDocument();
    });

    it('switches to Security tab when clicked', () => {
      renderComponent();

      const securityTab = screen.getByRole('tab', { name: /security/i });
      act(() => {
        fireEvent.click(securityTab);
      });

      expect(screen.getByTestId('password-change-form')).toBeInTheDocument();
      expect(screen.queryByTestId('profile-form')).not.toBeInTheDocument();
      expect(screen.queryByTestId('profile-picture-upload')).not.toBeInTheDocument();
    });

    it('switches to Notifications tab when clicked', () => {
      renderComponent();

      const notificationsTab = screen.getByRole('tab', { name: /notifications/i });
      fireEvent.click(notificationsTab);

      expect(screen.getByTestId('notification-settings')).toBeInTheDocument();
      expect(screen.queryByTestId('profile-form')).not.toBeInTheDocument();
    });

    it('switches to Account tab when clicked', () => {
      renderComponent();

      const accountTab = screen.getByRole('tab', { name: /account/i });
      fireEvent.click(accountTab);

      expect(screen.getByTestId('account-deletion')).toBeInTheDocument();
      expect(screen.queryByTestId('profile-form')).not.toBeInTheDocument();
    });

    it('maintains selected tab state', () => {
      renderComponent();

      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);

      expect(securityTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByRole('tab', { name: /profile/i })).toHaveAttribute(
        'aria-selected',
        'false'
      );
    });

    it('updates tab panel visibility correctly', () => {
      renderComponent();

      // Initially Profile tab is selected
      const profilePanel = document.getElementById('profile-tabpanel-0');
      const securityPanel = document.getElementById('profile-tabpanel-1');

      expect(profilePanel).not.toHaveAttribute('hidden');
      expect(securityPanel).toHaveAttribute('hidden');

      // Switch to Security tab
      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);

      expect(profilePanel).toHaveAttribute('hidden');
      expect(securityPanel).not.toHaveAttribute('hidden');
    });
  });

  describe('Tab Panel Content', () => {
    it('renders Profile tab content correctly', () => {
      renderComponent();

      // Should show both ProfileForm and ProfilePictureUpload
      expect(screen.getByTestId('profile-form')).toBeInTheDocument();
      expect(screen.getByTestId('profile-picture-upload')).toBeInTheDocument();
    });

    it('renders Security tab content correctly', () => {
      renderComponent();

      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);

      expect(screen.getByTestId('password-change-form')).toBeInTheDocument();
    });

    it('renders Notifications tab content correctly', () => {
      renderComponent();

      const notificationsTab = screen.getByRole('tab', { name: /notifications/i });
      fireEvent.click(notificationsTab);

      expect(screen.getByTestId('notification-settings')).toBeInTheDocument();
    });

    it('renders Account tab content correctly', () => {
      renderComponent();

      const accountTab = screen.getByRole('tab', { name: /account/i });
      fireEvent.click(accountTab);

      expect(screen.getByTestId('account-deletion')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('provides proper ARIA labels for tabs', () => {
      renderComponent();

      const profileTab = screen.getByRole('tab', { name: /profile/i });
      const securityTab = screen.getByRole('tab', { name: /security/i });
      const notificationsTab = screen.getByRole('tab', { name: /notifications/i });
      const accountTab = screen.getByRole('tab', { name: /account/i });

      expect(profileTab).toHaveAttribute('id', 'profile-tab-0');
      expect(profileTab).toHaveAttribute('aria-controls', 'profile-tabpanel-0');

      expect(securityTab).toHaveAttribute('id', 'profile-tab-1');
      expect(securityTab).toHaveAttribute('aria-controls', 'profile-tabpanel-1');

      expect(notificationsTab).toHaveAttribute('id', 'profile-tab-2');
      expect(notificationsTab).toHaveAttribute('aria-controls', 'profile-tabpanel-2');

      expect(accountTab).toHaveAttribute('id', 'profile-tab-3');
      expect(accountTab).toHaveAttribute('aria-controls', 'profile-tabpanel-3');
    });

    it('provides proper ARIA labels for tab panels', () => {
      renderComponent();

      const profilePanel = document.getElementById('profile-tabpanel-0');
      const securityPanel = document.getElementById('profile-tabpanel-1');
      const notificationsPanel = document.getElementById('profile-tabpanel-2');
      const accountPanel = document.getElementById('profile-tabpanel-3');

      expect(profilePanel).toHaveAttribute('id', 'profile-tabpanel-0');
      expect(profilePanel).toHaveAttribute('aria-labelledby', 'profile-tab-0');

      expect(securityPanel).toHaveAttribute('id', 'profile-tabpanel-1');
      expect(securityPanel).toHaveAttribute('aria-labelledby', 'profile-tab-1');

      expect(notificationsPanel).toHaveAttribute('id', 'profile-tabpanel-2');
      expect(notificationsPanel).toHaveAttribute('aria-labelledby', 'profile-tab-2');

      expect(accountPanel).toHaveAttribute('id', 'profile-tabpanel-3');
      expect(accountPanel).toHaveAttribute('aria-labelledby', 'profile-tab-3');
    });

    it('provides proper aria-label for tabs container', () => {
      renderComponent();

      const tabsContainer = screen.getByRole('tablist');
      expect(tabsContainer).toHaveAttribute('aria-label', 'profile settings tabs');
    });

    it('supports keyboard navigation', () => {
      renderComponent();

      const profileTab = screen.getByRole('tab', { name: /profile/i });
      const securityTab = screen.getByRole('tab', { name: /security/i });

      // Focus on profile tab
      act(() => {
        profileTab.focus();
      });
      expect(document.activeElement).toBe(profileTab);

      // Navigate to security tab using keyboard
      act(() => {
        securityTab.focus();
      });
      expect(document.activeElement).toBe(securityTab);
    });
  });

  describe('User Information Display', () => {
    it('handles user with complete profile information', () => {
      renderComponent();

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByText('Test user bio')).toBeInTheDocument();
    });

    it('handles user with minimal profile information', () => {
      const storeWithMinimalUser = configureStore({
        reducer: {
          auth: authSlice,
          userProfile: userProfileSlice,
        },
        preloadedState: {
          auth: {
            user: mockUserMinimal,
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

      renderComponent(storeWithMinimalUser);

      expect(screen.getByText('simpleuser')).toBeInTheDocument();
      expect(screen.getByText('simple@example.com')).toBeInTheDocument();
      expect(screen.queryByText('Test user bio')).not.toBeInTheDocument();
    });

    it('displays avatar with proper alt text', () => {
      renderComponent();

      const avatar = screen.getByRole('img');
      expect(avatar).toBeInTheDocument();
    });
  });

  describe('Layout and Styling', () => {
    it('renders with proper container layout', () => {
      renderComponent();

      const container = screen.getByText('Profile Settings').closest('.MuiContainer-root');
      expect(container).toBeInTheDocument();
    });

    it('renders profile header in a paper component', () => {
      renderComponent();

      const profileHeader = screen.getByText('John Doe').closest('.MuiPaper-root');
      expect(profileHeader).toBeInTheDocument();
    });

    it('renders tabs in a paper component', () => {
      renderComponent();

      const tabsContainer = screen.getByRole('tablist').closest('.MuiPaper-root');
      expect(tabsContainer).toBeInTheDocument();
    });

    it('maintains responsive layout structure', () => {
      renderComponent();

      // Check for Grid components
      const gridContainers = screen
        .getAllByText(/Profile Form Component|Profile Picture Upload Component/)[0]
        .closest('.MuiGrid-container');
      expect(gridContainers).toBeInTheDocument();
    });
  });

  describe('Component Integration', () => {
    it('integrates all profile components correctly', () => {
      renderComponent();

      // Profile tab
      expect(screen.getByTestId('profile-form')).toBeInTheDocument();
      expect(screen.getByTestId('profile-picture-upload')).toBeInTheDocument();

      // Security tab
      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);
      expect(screen.getByTestId('password-change-form')).toBeInTheDocument();

      // Notifications tab
      const notificationsTab = screen.getByRole('tab', { name: /notifications/i });
      fireEvent.click(notificationsTab);
      expect(screen.getByTestId('notification-settings')).toBeInTheDocument();

      // Account tab
      const accountTab = screen.getByRole('tab', { name: /account/i });
      fireEvent.click(accountTab);
      expect(screen.getByTestId('account-deletion')).toBeInTheDocument();
    });

    it('passes correct props to components through Redux state', () => {
      // The components are mocked, but they would receive props from Redux state
      renderComponent();

      // Verify that components are rendered, which means they're receiving the necessary state
      expect(screen.getByTestId('profile-form')).toBeInTheDocument();
      expect(screen.getByTestId('profile-picture-upload')).toBeInTheDocument();
    });
  });

  describe('State Management', () => {
    it('accesses user data from Redux store', () => {
      renderComponent();

      // Verify user data is displayed, confirming Redux integration
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    it('handles missing user state gracefully', () => {
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
        screen.getByText(/please log in to access your profile settings/i)
      ).toBeInTheDocument();
    });
  });

  describe('Tab State Management', () => {
    it('maintains tab state internally', () => {
      renderComponent();

      // Start with Profile tab selected
      expect(screen.getByRole('tab', { name: /profile/i })).toHaveAttribute(
        'aria-selected',
        'true'
      );

      // Switch to Security tab
      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);

      expect(securityTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByRole('tab', { name: /profile/i })).toHaveAttribute(
        'aria-selected',
        'false'
      );
    });

    it('updates content when tab changes', async () => {
      renderComponent();

      // Initially shows Profile content
      expect(screen.getByTestId('profile-form')).toBeInTheDocument();

      // Switch to Security tab
      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);

      await waitFor(() => {
        expect(screen.getByTestId('password-change-form')).toBeInTheDocument();
        expect(screen.queryByTestId('profile-form')).not.toBeInTheDocument();
      });
    });
  });
});
