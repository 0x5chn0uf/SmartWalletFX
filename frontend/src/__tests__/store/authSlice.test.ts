import authReducer, { logout } from '../../store/authSlice';

// Inline AuthState type for test
interface AuthState {
  token: string | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

describe('authSlice', () => {
  it('should return the initial state', () => {
    expect(authReducer(undefined, { type: undefined })).toEqual({
      token: null,
      status: 'idle',
      error: null,
    });
  });

  it('should handle logout', () => {
    const prevState: AuthState = { token: 'abc123', status: 'idle', error: null };
    expect(authReducer(prevState, logout())).toEqual({
      token: null,
      status: 'idle',
      error: null,
    });
  });
}); 