import { renderHook, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { useTimeline } from '../../hooks/useTimeline';
import * as defi from '../../services/defi';

vi.mock('../../services/defi');
const getTimeline = defi.getTimeline as unknown as vi.Mock;

describe('useTimeline', () => {
  const options = { address: '0x123', from: 0, to: 0, enabled: false };

  it('initializes with default state when disabled', () => {
    const { result } = renderHook(() => useTimeline(options));
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('fetches timeline data when enabled', async () => {
    (getTimeline as any).mockResolvedValue([{ timestamp: 1 }]);
    const { result } = renderHook(() => useTimeline({ address: 'a', from: 1, to: 2, enabled: true }));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual([{ timestamp: 1 }]);
    expect(result.current.error).toBeNull();
  });

  it('handles fetch errors', async () => {
    (getTimeline as any).mockRejectedValue(new Error('fail'));
    const { result } = renderHook(() => useTimeline({ address: 'a', from: 1, to: 2, enabled: true }));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('fail');
    expect(result.current.data).toBeNull();
  });
});
