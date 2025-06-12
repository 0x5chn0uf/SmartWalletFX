import { useEffect, useState } from 'react';
import { getTimeline } from '../services/defi';
import { PortfolioSnapshot } from '../types/timeline';

interface UseTimelineOptions {
  address: string;
  from: number;
  to: number;
  interval?: 'none' | 'daily' | 'weekly';
  enabled?: boolean;
}

export function useTimeline({ address, from, to, interval, enabled = true }: UseTimelineOptions) {
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
        const snapshots = (await getTimeline(address, {
          from_ts: from,
          to_ts: to,
          interval: interval ?? 'none',
          raw: true,
        })) as PortfolioSnapshot[];
        setData(snapshots);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    fetchTimeline();
  }, [address, from, to, interval, enabled]);

  return { data, loading, error };
} 