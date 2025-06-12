import { useEffect, useState } from 'react';
import { getTimeline } from '../services/defi';
import { PortfolioSnapshot } from '../types/timeline';

interface UseTimelineOptions {
  address: string;
  from: number;
  to: number;
}

export function useTimeline({ address, from, to }: UseTimelineOptions) {
  const [data, setData] = useState<PortfolioSnapshot[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function fetchTimeline() {
      setLoading(true);
      setError(null);
      try {
        const snapshots = (await getTimeline(address, {
          from_ts: from,
          to_ts: to,
          raw: true,
        })) as PortfolioSnapshot[];
        if (mounted) setData(snapshots);
      } catch (err) {
        if (mounted) setError((err as Error).message);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchTimeline();
    return () => {
      mounted = false;
    };
  }, [address, from, to]);

  return { data, loading, error };
} 