import api from './api';
import { PortfolioSnapshot, TimelineResponse } from '../types/timeline';

interface TimelineQueryParams {
  startDate?: string;
  endDate?: string;
  interval?: string;
  from_ts?: number;
  to_ts?: number;
  limit?: number;
  offset?: number;
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

export async function getPortfolioTimeline(params: TimelineQueryParams = {}): Promise<TimelineResponse> {
  const response = await api.get<TimelineResponse>('/defi/portfolio/timeline', { params });
  return response.data;
}

export async function getPortfolioSnapshot(): Promise<PortfolioSnapshot> {
  const response = await api.get<PortfolioSnapshot>('/defi/portfolio/snapshot');
  return response.data;
}
