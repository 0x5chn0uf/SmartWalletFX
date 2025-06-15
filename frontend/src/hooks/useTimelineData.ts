import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { getTimeline } from '../services/defi';
import { PortfolioSnapshot, TimelineResponse } from '../types/timeline';

export interface UseTimelineParams {
  address: string;
  /** unix seconds */
  from: number;
  /** unix seconds */
  to: number;
  interval?: 'none' | 'daily' | 'weekly';
  /** return raw snapshots array instead of wrapped response */
  raw?: boolean;
}

export function useTimelineData(
  params: UseTimelineParams,
  options?: Partial<UseQueryOptions<PortfolioSnapshot[] | TimelineResponse, Error>>
) {
  const { address, from, to, interval = 'none', raw = true } = params;

  return useQuery<PortfolioSnapshot[] | TimelineResponse, Error>({
    queryKey: ['timeline', address, from, to, interval, raw],
    queryFn: () => getTimeline(address, { from_ts: from, to_ts: to, interval, raw }),
    staleTime: 1000 * 60, // 1 min
    enabled: Boolean(address),
    ...options,
  });
}
