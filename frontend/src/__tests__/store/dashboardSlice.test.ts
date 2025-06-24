import dashboardReducer from '../../store/dashboardSlice';

// Inline types for test
interface Overview {
  totalWallets: number;
  totalBalance: number;
  dailyVolume: number;
  chart: Array<{ date: string; balance: number }>;
}
interface DashboardState {
  overview: Overview | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

describe('dashboardSlice', () => {
  it('should return the initial state', () => {
    expect(dashboardReducer(undefined, { type: undefined })).toEqual({
      overview: null,
      status: 'idle',
      error: null,
    });
  });

  it('should handle fetchDashboardOverview.fulfilled', () => {
    const prevState: DashboardState = { overview: null, status: 'idle', error: null };
    const overview: Overview = {
      totalWallets: 2,
      totalBalance: 1000,
      dailyVolume: 100,
      chart: [],
    };
    const nextState = dashboardReducer(prevState, {
      type: 'dashboard/fetchOverview/fulfilled',
      payload: overview,
    });
    expect(nextState.overview).toEqual(overview);
    expect(nextState.status).toBe('succeeded');
    expect(nextState.error).toBeNull();
  });
}); 