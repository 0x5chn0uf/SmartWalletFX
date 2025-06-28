import walletsReducer from '../../store/walletsSlice';

// Inline types for test
interface Wallet {
  id: string;
  name: string;
  address: string;
  balance: number;
  currency: string;
  lastUpdated: string;
}
interface WalletsState {
  wallets: Wallet[];
  total: number;
  page: number;
  limit: number;
  search: string;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}
interface WalletsResponse {
  wallets: Wallet[];
  total: number;
  page: number;
  limit: number;
}

describe('walletsSlice', () => {
  it('should return the initial state', () => {
    expect(walletsReducer(undefined, { type: undefined })).toEqual({
      wallets: [],
      total: 0,
      page: 1,
      limit: 10,
      search: '',
      status: 'idle',
      error: null,
    });
  });

  it('should handle fetchWallets.fulfilled', () => {
    const prevState: WalletsState = {
      wallets: [],
      total: 0,
      page: 1,
      limit: 10,
      search: '',
      status: 'idle',
      error: null,
    };
    const wallets: Wallet[] = [
      { id: '1', name: 'Wallet 1', address: '', balance: 100, currency: 'USD', lastUpdated: '' },
      { id: '2', name: 'Wallet 2', address: '', balance: 200, currency: 'EUR', lastUpdated: '' },
    ];
    const payload: WalletsResponse = { wallets, total: 2, page: 1, limit: 10 };
    const nextState = walletsReducer(prevState, {
      type: 'wallets/fetchWallets/fulfilled',
      payload,
    });
    expect(nextState.wallets).toEqual(wallets);
    expect(nextState.total).toBe(2);
    expect(nextState.status).toBe('succeeded');
    expect(nextState.error).toBeNull();
  });
});
