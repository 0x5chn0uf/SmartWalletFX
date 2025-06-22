export interface Position {
  asset: string;
  amount: number;
  value: number;
}

export interface PortfolioSnapshot {
  timestamp: number; // Unix timestamp
  total_value: number;
  positions: Position[];
  cash: number;
}
