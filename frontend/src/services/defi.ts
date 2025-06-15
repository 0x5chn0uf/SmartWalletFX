import { api } from './api';
import { PortfolioSnapshot, TimelineResponse } from '../types/timeline';

interface TimelineQueryParams {
  from_ts: number;
  to_ts: number;
  limit?: number;
  offset?: number;
  interval?: 'none' | 'daily' | 'weekly';
  raw?: boolean;
}

export async function getTimeline(
  address: string,
  params: TimelineQueryParams
): Promise<PortfolioSnapshot[] | TimelineResponse> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      searchParams.set(key, String(value));
    }
  });
  const search = searchParams.toString();
  const url = `/defi/timeline/${address}?${search}`;
  const response = await api.get<PortfolioSnapshot[] | TimelineResponse>(url);
  return response.data;
}
