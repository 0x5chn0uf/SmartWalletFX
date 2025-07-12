// @ts-nocheck
import reducer from '../../store/emailVerificationSlice';

describe('emailVerificationSlice reducer', () => {
  const initial = { status: 'idle', error: null };

  it('handles verifyEmail lifecycle', () => {
    let state = reducer(initial, { type: 'emailVerification/verify/pending' });
    expect(state.status).toBe('loading');
    state = reducer(state, { type: 'emailVerification/verify/fulfilled' });
    expect(state.status).toBe('succeeded');
    state = reducer(state, {
      type: 'emailVerification/verify/rejected',
      error: { message: 'err' },
    });
    expect(state.status).toBe('failed');
    expect(state.error).toBe('err');
  });

  it('handles resendVerification lifecycle', () => {
    let state = reducer(initial, { type: 'emailVerification/resend/pending' });
    expect(state.status).toBe('loading');
    state = reducer(state, { type: 'emailVerification/resend/fulfilled' });
    expect(state.status).toBe('succeeded');
  });
});
