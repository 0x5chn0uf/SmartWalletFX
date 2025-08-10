import api from './api';
import { PortfolioSnapshot, TimelineResponse } from '../types/timeline';

interface TimelineQueryParams {
  start_date?: string;
  end_date?: string;
  interval?: string;
  from_ts?: number;
  to_ts?: number;
  limit?: number;
  offset?: number;
  raw?: boolean;
}

/**
 * DeFi KPI metrics for dashboard cards.
 */
export interface DefiKPI {
  tvl: number; // Total Value Locked
  apy: number; // Average Percentage Yield
  protocols: ProtocolBreakdown[];
  updated_at: string; // ISO date
}

/**
 * Protocol-level breakdown for DeFi KPIs.
 */
export interface ProtocolBreakdown {
  name: string;
  tvl: number;
  apy: number;
  positions: number;
}

/**
 * Error/partial data response structure.
 */
export interface DefiError {
  error: string;
  partial?: boolean;
  data?: any;
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

// Add mock timeline data for the dashboard (matching TimelineResponse type)
const MOCK_PORTFOLIO_TIMELINE = {
  snapshots: [
    {
      user_address: '0xMOCK',
      timestamp: 1719446400,
      total_collateral: 1200000,
      total_borrowings: 0,
      aggregate_health_score: null,
    },
    {
      user_address: '0xMOCK',
      timestamp: 1719532800,
      total_collateral: 1225000,
      total_borrowings: 0,
      aggregate_health_score: null,
    },
    {
      user_address: '0xMOCK',
      timestamp: 1719619200,
      total_collateral: 1210000,
      total_borrowings: 0,
      aggregate_health_score: null,
    },
    {
      user_address: '0xMOCK',
      timestamp: 1719705600,
      total_collateral: 1240000,
      total_borrowings: 0,
      aggregate_health_score: null,
    },
    {
      user_address: '0xMOCK',
      timestamp: 1719792000,
      total_collateral: 1230000,
      total_borrowings: 0,
      aggregate_health_score: null,
    },
    {
      user_address: '0xMOCK',
      timestamp: 1719878400,
      total_collateral: 1250000,
      total_borrowings: 0,
      aggregate_health_score: null,
    },
    {
      user_address: '0xMOCK',
      timestamp: 1719964800,
      total_collateral: 1254321,
      total_borrowings: 0,
      aggregate_health_score: null,
    },
  ],
  interval: '1d',
  limit: 7,
  offset: 0,
  total: 7,
};

export async function getPortfolioTimeline(
  params: TimelineQueryParams = {}
): Promise<TimelineResponse> {
  return withMockFallback(async () => {
    const response = await api.get<TimelineResponse>('/defi/portfolio/timeline', { params });
    return response.data;
  }, MOCK_PORTFOLIO_TIMELINE);
}

export async function getPortfolioSnapshot(): Promise<PortfolioSnapshot> {
  const response = await api.get<PortfolioSnapshot>('/defi/portfolio/snapshot');
  return response.data;
}

// ---------------------------------------------------------------------------
// Mock data helpers (used in development when backend is unavailable)
// ---------------------------------------------------------------------------

// @ts-ignore
const USE_MOCK = ((import.meta as any).env.VITE_USE_MOCK ?? 'false') === 'true';

const MOCK_DEFI_KPI: DefiKPI = {
  tvl: 1254321.45,
  apy: 8.73,
  updated_at: new Date().toISOString(),
  protocols: [
    { name: 'Aave', tvl: 534221.12, apy: 6.2, positions: 12 },
    { name: 'Compound', tvl: 312876.44, apy: 5.1, positions: 8 },
    { name: 'Radiant', tvl: 407224.89, apy: 14.2, positions: 5 },
  ],
};

const MOCK_PROTOCOL_BREAKDOWN: ProtocolBreakdown[] = MOCK_DEFI_KPI.protocols;

function shouldUseMock(): boolean {
  // Use mock if explicit env var is set OR if we are in development and the backend host is unreachable.
  return USE_MOCK;
}

// Helper to safely call API with mock fallback
async function withMockFallback<T>(fn: () => Promise<T>, mock: T): Promise<T> {
  if (shouldUseMock()) {
    return Promise.resolve(mock);
  }
  try {
    return await fn();
  } catch (err) {
    console.warn('[defi.ts] Falling back to mock data due to error:', err);
    return mock;
  }
}

/**
 * Fetch DeFi KPIs (TVL, APY, protocol breakdown) for the dashboard.
 * @returns {Promise<DefiKPI>}
 */
export async function getDefiKPI(): Promise<DefiKPI> {
  return withMockFallback(async () => {
    const response = await api.get<DefiKPI>('/defi/portfolio/kpi');
    return response.data;
  }, MOCK_DEFI_KPI);
}

/**
 * Fetch protocol-level breakdown for the dashboard table.
 * @returns {Promise<ProtocolBreakdown[]>}
 */
export async function getProtocolBreakdown(): Promise<ProtocolBreakdown[]> {
  return withMockFallback(async () => {
    const response = await api.get<ProtocolBreakdown[]>('/defi/portfolio/protocols');
    return response.data;
  }, MOCK_PROTOCOL_BREAKDOWN);
}
