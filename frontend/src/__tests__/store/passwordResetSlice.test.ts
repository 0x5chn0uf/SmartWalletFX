// @ts-nocheck
import reducer from '../../store/passwordResetSlice';

describe('passwordResetSlice reducer', () => {
  const initial = { status: 'idle', error: null };

  it('handles requestReset lifecycle', () => {
    const pending = reducer(initial, { type: 'passwordReset/request/pending' });
    expect(pending.status).toBe('loading');

    const fulfilled = reducer(pending, { type: 'passwordReset/request/fulfilled' });
    expect(fulfilled.status).toBe('succeeded');

    const failed = reducer(fulfilled, {
      type: 'passwordReset/request/rejected',
      error: { message: 'err' },
    });
    expect(failed.status).toBe('failed');
    expect(failed.error).toBe('err');
  });

  it('handles resetPassword lifecycle', () => {
    const pending = reducer(initial, { type: 'passwordReset/reset/pending' });
    expect(pending.status).toBe('loading');
    const fulfilled = reducer(pending, { type: 'passwordReset/reset/fulfilled' });
    expect(fulfilled.status).toBe('succeeded');
  });
});
