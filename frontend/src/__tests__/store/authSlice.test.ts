import authReducer, { logout } from '../../store/authSlice';

// Inline AuthState type for test
interface AuthState {
  isAuthenticated: boolean;
  user: any;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

describe('authSlice', () => {
  it('should return the initial state', () => {
    expect(authReducer(undefined, { type: undefined })).toEqual({
      isAuthenticated: false,
      user: null,
      status: 'idle',
      error: null,
    });
  });

  it('should handle logout', () => {
    const prevState: AuthState = {
      isAuthenticated: true,
      user: { id: 1 },
      status: 'idle',
      error: null,
    };
    expect(authReducer(prevState, logout())).toEqual({
      isAuthenticated: false,
      user: null,
      status: 'idle',
      error: null,
    });
  });
});
