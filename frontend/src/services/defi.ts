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
  const search = new URLSearchParams(params as any).toString();
  const url = `/defi/timeline/${address}?${search}`;
  const response = await api.get<PortfolioSnapshot[] | TimelineResponse>(url);
  return response.data;
} 