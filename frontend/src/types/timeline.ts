export interface PortfolioSnapshot {
  user_address: string;
  timestamp: number;
  total_collateral: number;
  total_borrowings: number;
  aggregate_health_score?: number | null;
  // add more fields as required by chart later
}

export interface TimelineResponse {
  snapshots: PortfolioSnapshot[];
  interval: string;
  limit: number;
  offset: number;
  total: number;
} 