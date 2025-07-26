import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../theme';
import authReducer from '../../../store/authSlice';
import userProfileReducer, { updateUserProfile } from '../../../store/slices/userProfileSlice';
import ProfileForm from '../../../components/profile/ProfileForm';

// Mock the user profile slice actions
vi.mock('../../../store/slices/userProfileSlice', async importOriginal => {
  const actual = await importOriginal();
  const mockUpdateUserProfile = vi.fn(() => ({ type: 'userProfile/updateUserProfile/pending' }));
  mockUpdateUserProfile.fulfilled = { type: 'userProfile/updateUserProfile/fulfilled' };
  mockUpdateUserProfile.pending = { type: 'userProfile/updateUserProfile/pending' };
  mockUpdateUserProfile.rejected = { type: 'userProfile/updateUserProfile/rejected' };

  const mockUpdateNotificationPreferences = vi.fn(() => ({
    type: 'userProfile/updateNotificationPreferences/pending',
  }));
  mockUpdateNotificationPreferences.fulfilled = {
    type: 'userProfile/updateNotificationPreferences/fulfilled',
  };

  const mockUploadProfilePicture = vi.fn(() => ({
    type: 'userProfile/uploadProfilePicture/pending',
  }));
  mockUploadProfilePicture.fulfilled = { type: 'userProfile/uploadProfilePicture/fulfilled' };

  const mockDeleteProfilePicture = vi.fn(() => ({
    type: 'userProfile/deleteProfilePicture/pending',
  }));
  mockDeleteProfilePicture.fulfilled = { type: 'userProfile/deleteProfilePicture/fulfilled' };

  return {
    ...actual,
    updateUserProfile: mockUpdateUserProfile,
    updateNotificationPreferences: mockUpdateNotificationPreferences,
    uploadProfilePicture: mockUploadProfilePicture,
    deleteProfilePicture: mockDeleteProfilePicture,
  };
});

const mockUser = {
  id: 'user-123',
  username: 'testuser',
  email: 'test@example.com',
  email_verified: true,
  first_name: 'John',
  last_name: 'Doe',
  bio: 'Test bio',
  timezone: 'UTC',
  preferred_currency: 'USD',
  profile_picture_url: null,
  notification_preferences: null,
};

const renderProfileForm = (initialState = {}) => {
  const defaultState = {
    auth: {
      isAuthenticated: true,
      user: mockUser,
      status: 'succeeded',
      error: null,
    },
    userProfile: {
      loading: false,
      error: null,
      success: false,
    },
  };

  const store = configureStore({
    reducer: {
      auth: authReducer,
      userProfile: userProfileReducer,
    },
    preloadedState: { ...defaultState, ...initialState } as any,
  });

  return render(
    <Provider store={store}>
      <ThemeProvider theme={createAppTheme()}>
        <ProfileForm />
      </ThemeProvider>
    </Provider>
  );
};

describe('ProfileForm', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the form with user data', () => {
    renderProfileForm();

    expect(screen.getByDisplayValue('John')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test bio')).toBeInTheDocument();
    expect(screen.getByDisplayValue('UTC')).toBeInTheDocument();
    expect(screen.getByDisplayValue('USD')).toBeInTheDocument();
  });

  it('shows login message when user is not authenticated', () => {
    renderProfileForm({
      auth: {
        isAuthenticated: false,
        user: null,
        status: 'succeeded',
        error: null,
      },
    });

    expect(screen.getByText('Please log in to edit your profile.')).toBeInTheDocument();
  });

  it('allows editing form fields', async () => {
    renderProfileForm();

    const firstNameField = screen.getByLabelText('First Name');
    const lastNameField = screen.getByLabelText('Last Name');
    const bioField = screen.getByLabelText('Bio');

    // Use fireEvent for more reliable text input in tests
    fireEvent.change(firstNameField, { target: { value: 'Jane' } });
    await waitFor(() => {
      expect(firstNameField).toHaveValue('Jane');
    });

    fireEvent.change(lastNameField, { target: { value: 'Smith' } });
    await waitFor(() => {
      expect(lastNameField).toHaveValue('Smith');
    });

    fireEvent.change(bioField, { target: { value: 'Updated bio description' } });
    await waitFor(() => {
      expect(bioField).toHaveValue('Updated bio description');
    });
  });

  it('shows character count for bio field', () => {
    renderProfileForm();

    const bioField = screen.getByLabelText('Bio');
    expect(screen.getByText('8/1000 characters')).toBeInTheDocument(); // 'Test bio' = 8 chars
  });

  it('validates field lengths and shows errors', async () => {
    renderProfileForm();

    const firstNameField = screen.getByLabelText('First Name');
    const bioField = screen.getByLabelText('Bio');
    const saveButton = screen.getByRole('button', { name: /save changes/i });

    // Test first name too long
    fireEvent.change(firstNameField, { target: { value: 'a'.repeat(101) } });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('First name must be 100 characters or less')).toBeInTheDocument();
    });

    // Test bio too long
    fireEvent.change(bioField, { target: { value: 'a'.repeat(1001) } });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Bio must be 1000 characters or less')).toBeInTheDocument();
    });
  });

  it('allows selecting timezone from dropdown', async () => {
    renderProfileForm();

    const timezoneField = screen.getByLabelText('Timezone');
    await user.click(timezoneField);

    // Wait for dropdown to open
    await waitFor(() => {
      expect(screen.getByText('America/New_York')).toBeInTheDocument();
    });

    await user.click(screen.getByText('America/New_York'));

    // For MUI Select, check the displayed value in the input element
    await waitFor(() => {
      expect(screen.getByDisplayValue('America/New_York')).toBeInTheDocument();
    });
  });

  it('allows selecting currency from dropdown', async () => {
    renderProfileForm();

    const currencyField = screen.getByLabelText('Preferred Currency');
    await user.click(currencyField);

    // Wait for dropdown to open
    await waitFor(() => {
      expect(screen.getByText('EUR - Euro')).toBeInTheDocument();
    });

    await user.click(screen.getByText('EUR - Euro'));

    // For MUI Select, check the displayed value in the input element
    await waitFor(() => {
      expect(screen.getByDisplayValue('EUR')).toBeInTheDocument();
    });
  });

  it('submits the form with updated data', async () => {
    renderProfileForm();

    const firstNameField = screen.getByLabelText('First Name');
    const saveButton = screen.getByRole('button', { name: /save changes/i });

    fireEvent.change(firstNameField, { target: { value: 'UpdatedName' } });
    await user.click(saveButton);

    await waitFor(() => {
      expect(updateUserProfile).toHaveBeenCalledWith({
        first_name: 'UpdatedName',
        last_name: 'Doe',
        bio: 'Test bio',
        timezone: 'UTC',
        preferred_currency: 'USD',
      });
    });
  });

  it('filters out empty values before submitting', async () => {
    renderProfileForm({
      auth: {
        isAuthenticated: true,
        user: { ...mockUser, first_name: '', last_name: '' },
        status: 'succeeded',
        error: null,
      },
    });

    const bioField = screen.getByLabelText('Bio');
    const saveButton = screen.getByRole('button', { name: /save changes/i });

    fireEvent.change(bioField, { target: { value: 'Only bio updated' } });
    await user.click(saveButton);

    await waitFor(() => {
      expect(updateUserProfile).toHaveBeenCalledWith({
        bio: 'Only bio updated',
        timezone: 'UTC',
        preferred_currency: 'USD',
      });
    });
  });

  it('resets form to original values', async () => {
    renderProfileForm();

    const firstNameField = screen.getByLabelText('First Name');
    const resetButton = screen.getByRole('button', { name: /reset/i });

    // Change the value
    fireEvent.change(firstNameField, { target: { value: 'ChangedName' } });

    // Wait for the change to be applied
    await waitFor(() => {
      expect(firstNameField).toHaveValue('ChangedName');
    });

    // Reset the form
    await user.click(resetButton);

    // Check that the form reset to original values
    await waitFor(() => {
      expect(firstNameField).toHaveValue('John');
    });
  });

  it('shows loading state during submission', () => {
    renderProfileForm({
      userProfile: {
        loading: true,
        error: null,
        success: false,
      },
    });

    const saveButton = screen.getByRole('button', { name: /saving.../i });
    expect(saveButton).toBeDisabled();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows success message after successful update', () => {
    renderProfileForm({
      userProfile: {
        loading: false,
        error: null,
        success: true,
      },
    });

    expect(screen.getByText('Profile updated successfully!')).toBeInTheDocument();
  });

  it('shows error message when update fails', () => {
    renderProfileForm({
      userProfile: {
        loading: false,
        error: 'Update failed',
        success: false,
      },
    });

    expect(screen.getByText('Update failed')).toBeInTheDocument();
  });

  it('disables form fields during loading', () => {
    renderProfileForm({
      userProfile: {
        loading: true,
        error: null,
        success: false,
      },
    });

    expect(screen.getByLabelText('First Name')).toBeDisabled();
    expect(screen.getByLabelText('Last Name')).toBeDisabled();
    expect(screen.getByLabelText('Bio')).toBeDisabled();

    // For MUI Select, check for aria-disabled attribute
    const timezoneField = screen.getByLabelText('Timezone');
    const currencyField = screen.getByLabelText('Preferred Currency');

    expect(timezoneField).toHaveAttribute('aria-disabled', 'true');
    expect(currencyField).toHaveAttribute('aria-disabled', 'true');
  });
});
