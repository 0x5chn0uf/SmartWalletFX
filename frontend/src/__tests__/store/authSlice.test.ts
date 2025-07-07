// @ts-nocheck
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

  it('handles login pending/fulfilled/rejected actions', () => {
    const initial = { isAuthenticated: false, user: null, status: 'idle', error: null };

    const pendingAction = { type: 'auth/login/pending' };
    let state = authReducer(initial, pendingAction);
    expect(state.status).toBe('loading');

    const fulfilledAction = { type: 'auth/login/fulfilled', payload: { id: '1' } };
    state = authReducer(state, fulfilledAction);
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual({ id: '1' });

    const rejectedAction = { type: 'auth/login/rejected', error: { message: 'oops' } };
    state = authReducer(state, rejectedAction);
    expect(state.status).toBe('failed');
    expect(state.error).toBe('oops');
  });
});
