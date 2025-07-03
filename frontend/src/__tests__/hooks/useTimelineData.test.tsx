import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as defi from '../../services/defi';
import { useTimelineData } from '../../hooks/useTimelineData';

describe('useTimelineData', () => {
  const queryClient = new QueryClient();
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  beforeAll(() => {
    vi.spyOn(defi, 'getTimeline').mockResolvedValue([]);
  });

  afterAll(() => {
    vi.restoreAllMocks();
  });

  it('returns query object and initial state', async () => {
    const params = { address: '0x123', from: 0, to: 0 };
    const { result } = renderHook(() => useTimelineData(params), { wrapper });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});
