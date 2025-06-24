import { mapSnapshotsToChartData } from '../../utils/timelineAdapter';

describe('mapSnapshotsToChartData', () => {
  it('should map portfolio snapshots to chart data', () => {
    const raw = [
      {
        timestamp: 1718668800, // 2024-06-18
        total_collateral: 100,
        total_borrowings: 50,
        aggregate_health_score: 0.9,
        user_address: '0x123',
      },
      {
        timestamp: 1718755200, // 2024-06-19
        total_collateral: 200,
        total_borrowings: 100,
        aggregate_health_score: null,
        user_address: '0x123',
      },
    ];
    const adapted = mapSnapshotsToChartData(raw);
    expect(adapted).toEqual([
      { ts: '2024-06-18', collateral: 100, borrowings: 50, health_score: 0.9 },
      { ts: '2024-06-19', collateral: 200, borrowings: 100, health_score: null },
    ]);
  });
}); 