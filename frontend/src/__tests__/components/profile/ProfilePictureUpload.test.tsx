import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../theme';
import authReducer from '../../../store/authSlice';
import userProfileReducer from '../../../store/slices/userProfileSlice';
import ProfilePictureUpload from '../../../components/profile/ProfilePictureUpload';

// Mock the user profile slice actions
vi.mock('../../../store/slices/userProfileSlice', async importOriginal => {
  const actual = await importOriginal();

  const mockUpdateUserProfile = vi.fn(() => ({ type: 'userProfile/updateUserProfile/pending' }));
  mockUpdateUserProfile.fulfilled = { type: 'userProfile/updateUserProfile/fulfilled' };

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
  mockUploadProfilePicture.pending = { type: 'userProfile/uploadProfilePicture/pending' };
  mockUploadProfilePicture.rejected = { type: 'userProfile/uploadProfilePicture/rejected' };

  const mockDeleteProfilePicture = vi.fn(() => ({
    type: 'userProfile/deleteProfilePicture/pending',
  }));
  mockDeleteProfilePicture.fulfilled = { type: 'userProfile/deleteProfilePicture/fulfilled' };
  mockDeleteProfilePicture.pending = { type: 'userProfile/deleteProfilePicture/pending' };
  mockDeleteProfilePicture.rejected = { type: 'userProfile/deleteProfilePicture/rejected' };

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

const mockUserWithPicture = {
  ...mockUser,
  profile_picture_url: 'http://localhost:8000/uploads/profile-123.jpg',
};

const renderProfilePictureUpload = (initialState = {}) => {
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
        <ProfilePictureUpload />
      </ThemeProvider>
    </Provider>
  );
};

// Helper to create a mock file
const createMockFile = (name: string, size: number, type: string) => {
  const file = new File(['file content'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};

describe('ProfilePictureUpload', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock FileReader
    const mockFileReader = {
      readAsDataURL: vi.fn(),
      result: 'data:image/jpeg;base64,fake-image-data',
      onload: null as any,
    };
    global.FileReader = vi.fn(() => mockFileReader) as any;
  });

  it('renders without user login message', () => {
    renderProfilePictureUpload({
      auth: {
        isAuthenticated: false,
        user: null,
        status: 'succeeded',
        error: null,
      },
    });

    expect(screen.getByText('Please log in to upload a profile picture.')).toBeInTheDocument();
  });

  it('renders upload interface when no profile picture exists', () => {
    renderProfilePictureUpload();

    expect(screen.getByText('Profile Picture')).toBeInTheDocument();
    expect(screen.getByText('Click to upload a profile picture')).toBeInTheDocument();
    expect(screen.getByText('Supports JPEG, PNG, GIF, WebP up to 5MB')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /choose file/i })).toBeInTheDocument();
  });

  it('renders edit and delete buttons when profile picture exists', () => {
    renderProfilePictureUpload({
      auth: {
        isAuthenticated: true,
        user: mockUserWithPicture,
        status: 'succeeded',
        error: null,
      },
    });

    expect(screen.getByLabelText('Change profile picture')).toBeInTheDocument();
    expect(screen.getByLabelText('Delete profile picture')).toBeInTheDocument();
  });

  it('shows user initial when no profile picture', () => {
    renderProfilePictureUpload();

    expect(screen.getByText('T')).toBeInTheDocument(); // First letter of username
  });

  it('validates file type and shows error for invalid files', async () => {
    renderProfilePictureUpload();

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const invalidFile = createMockFile('test.txt', 1024, 'text/plain');

    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [invalidFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(
        screen.getByText('Please select a valid image file (JPEG, PNG, GIF, or WebP)')
      ).toBeInTheDocument();
    });
  });

  it('validates file size and shows error for large files', async () => {
    renderProfilePictureUpload();

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const largeFile = createMockFile('large.jpg', 6 * 1024 * 1024, 'image/jpeg'); // 6MB

    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [largeFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('File size must be less than 5MB')).toBeInTheDocument();
    });
  });

  it('shows preview after valid file selection', async () => {
    renderProfilePictureUpload();

    const chooseFileButton = screen.getByRole('button', { name: /choose file/i });
    await user.click(chooseFileButton);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const validFile = createMockFile('test.jpg', 1024, 'image/jpeg');

    // Mock FileReader to trigger onload
    const mockFileReader = new FileReader();
    vi.spyOn(mockFileReader, 'readAsDataURL').mockImplementation(() => {
      setTimeout(() => {
        if (mockFileReader.onload) {
          mockFileReader.onload({ target: { result: 'data:image/jpeg;base64,fake-data' } } as any);
        }
      }, 0);
    });
    global.FileReader = vi.fn(() => mockFileReader) as any;

    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Ready to upload: test.jpg')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });
  });

  it('uploads file when upload button is clicked', async () => {
    const { uploadProfilePicture } = await import('../../../store/slices/userProfileSlice');
    renderProfilePictureUpload();

    const chooseFileButton = screen.getByRole('button', { name: /choose file/i });
    await user.click(chooseFileButton);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const validFile = createMockFile('test.jpg', 1024, 'image/jpeg');

    // Mock FileReader
    const mockFileReader = new FileReader();
    vi.spyOn(mockFileReader, 'readAsDataURL').mockImplementation(() => {
      setTimeout(() => {
        if (mockFileReader.onload) {
          mockFileReader.onload({ target: { result: 'data:image/jpeg;base64,fake-data' } } as any);
        }
      }, 0);
    });
    global.FileReader = vi.fn(() => mockFileReader) as any;

    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument();
    });

    const uploadButton = screen.getByRole('button', { name: /upload/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(uploadProfilePicture).toHaveBeenCalledWith(expect.any(FormData));
    });
  });

  it('cancels preview when cancel button is clicked', async () => {
    renderProfilePictureUpload();

    const chooseFileButton = screen.getByRole('button', { name: /choose file/i });
    await user.click(chooseFileButton);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const validFile = createMockFile('test.jpg', 1024, 'image/jpeg');

    // Mock FileReader
    const mockFileReader = new FileReader();
    vi.spyOn(mockFileReader, 'readAsDataURL').mockImplementation(() => {
      setTimeout(() => {
        if (mockFileReader.onload) {
          mockFileReader.onload({ target: { result: 'data:image/jpeg;base64,fake-data' } } as any);
        }
      }, 0);
    });
    global.FileReader = vi.fn(() => mockFileReader) as any;

    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(screen.getByText('Click to upload a profile picture')).toBeInTheDocument();
  });

  it('deletes profile picture when delete button is clicked', async () => {
    const { deleteProfilePicture } = await import('../../../store/slices/userProfileSlice');
    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => true);

    renderProfilePictureUpload({
      auth: {
        isAuthenticated: true,
        user: mockUserWithPicture,
        status: 'succeeded',
        error: null,
      },
    });

    const deleteButton = screen.getByLabelText('Delete profile picture');
    await user.click(deleteButton);

    await waitFor(() => {
      expect(deleteProfilePicture).toHaveBeenCalled();
    });

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('does not delete when user cancels confirmation', async () => {
    const { deleteProfilePicture } = await import('../../../store/slices/userProfileSlice');
    // Mock window.confirm to return false
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => false);

    renderProfilePictureUpload({
      auth: {
        isAuthenticated: true,
        user: mockUserWithPicture,
        status: 'succeeded',
        error: null,
      },
    });

    const deleteButton = screen.getByLabelText('Delete profile picture');
    await user.click(deleteButton);

    expect(deleteProfilePicture).not.toHaveBeenCalled();

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('shows loading state during upload', () => {
    renderProfilePictureUpload({
      userProfile: {
        loading: true,
        error: null,
        success: false,
      },
    });

    const chooseFileButton = screen.getByRole('button', { name: /choose file/i });
    expect(chooseFileButton).toBeDisabled();
  });

  it('shows error message when upload fails', () => {
    renderProfilePictureUpload({
      userProfile: {
        loading: false,
        error: 'Upload failed',
        success: false,
      },
    });

    expect(screen.getByText('Upload failed')).toBeInTheDocument();
  });

  it('disables buttons during loading', () => {
    renderProfilePictureUpload({
      auth: {
        isAuthenticated: true,
        user: mockUserWithPicture,
        status: 'succeeded',
        error: null,
      },
      userProfile: {
        loading: true,
        error: null,
        success: false,
      },
    });

    expect(screen.getByLabelText('Change profile picture')).toBeDisabled();
    expect(screen.getByLabelText('Delete profile picture')).toBeDisabled();
  });
});
