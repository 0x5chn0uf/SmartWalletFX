import dayjs from 'dayjs';
import { PortfolioSnapshot } from '../types/timeline';

export interface ChartDatum {
  ts: string;
  collateral: number;
  borrowings: number;
  health_score?: number | null;
}

export function mapSnapshotsToChartData(snapshots: PortfolioSnapshot[]): ChartDatum[] {
  return snapshots.map((s) => ({
    ts: dayjs.unix(s.timestamp).format('YYYY-MM-DD'),
    collateral: s.total_collateral,
    borrowings: s.total_borrowings,
    health_score: s.aggregate_health_score ?? null,
  }));
} 