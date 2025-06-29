import { renderHook } from '@testing-library/react';
import { useTimeline } from '../../hooks/useTimeline';

describe('useTimeline', () => {
  const options = { address: '0x123', from: 0, to: 0, enabled: false };

  it('returns data, loading, and error', () => {
    const { result } = renderHook(() => useTimeline(options));
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('loading');
    expect(result.current).toHaveProperty('error');
  });

  it('initial state is correct when disabled', () => {
    const { result } = renderHook(() => useTimeline(options));
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });
});
