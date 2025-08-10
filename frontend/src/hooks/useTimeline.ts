import { useEffect, useState } from 'react';
import { getTimeline } from '../services/defi';
import { PortfolioSnapshot } from '../types/timeline';

interface UseTimelineOptions {
  address: string;
  from?: number;
  to?: number;
  start_date?: string;
  end_date?: string;
  interval?: 'none' | 'daily' | 'weekly';
  enabled?: boolean;
}

export function useTimeline({ address, from, to, start_date, end_date, interval, enabled = true }: UseTimelineOptions) {
  const [data, setData] = useState<PortfolioSnapshot[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }

    async function fetchTimeline() {
      setLoading(true);
      setError(null);
      try {
        const params: any = {
          interval: interval ?? 'none',
          raw: true,
        };
        
        // Use date range if provided, otherwise use timestamps
        if (start_date || end_date) {
          if (start_date) params.start_date = start_date;
          if (end_date) params.end_date = end_date;
        } else {
          if (from) params.from_ts = from;
          if (to) params.to_ts = to;
        }

        const snapshots = (await getTimeline(address, params)) as PortfolioSnapshot[];
        setData(snapshots);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    fetchTimeline();
  }, [address, from, to, start_date, end_date, interval, enabled]);

  return { data, loading, error };
}
