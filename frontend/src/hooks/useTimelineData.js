import { useState, useEffect } from 'react';

/**
 * Temporary data-fetching hook for Portfolio Performance Timeline.
 * Will be replaced with React Query implementation once API wiring is finished.
 */
export function useTimelineData() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // TODO: replace with real call to getTimeline once parameters are defined
    // Simulate async fetch with small timeout
    const timer = setTimeout(() => {
      setData([]); // placeholder empty dataset
      setLoading(false);
    }, 300);

    return () => clearTimeout(timer);
  }, []);

  return { data, loading, error };
} 