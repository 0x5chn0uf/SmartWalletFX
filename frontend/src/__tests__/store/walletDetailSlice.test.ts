import walletDetailReducer from '../../store/walletDetailSlice';

// Inline types for test
interface WalletDetail {
  id: string;
  name: string;
  address: string;
  balance: number;
  currency: string;
  lastUpdated: string;
  trend: { date: string; balance: number }[];
}
interface WalletDetailState {
  wallet: WalletDetail | null;
  transactions: any[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

describe('walletDetailSlice', () => {
  it('should return the initial state', () => {
    expect(walletDetailReducer(undefined, { type: undefined })).toEqual({
      wallet: null,
      transactions: [],
      status: 'idle',
      error: null,
    });
  });

  it('should handle fetchWalletDetail.fulfilled', () => {
    const prevState: WalletDetailState = { wallet: null, transactions: [], status: 'idle', error: null };
    const wallet: WalletDetail = { id: '1', name: 'Test Wallet', address: '', balance: 1000, currency: 'USD', lastUpdated: '', trend: [] };
    const nextState = walletDetailReducer(prevState, {
      type: 'walletDetail/fetchWalletDetail/fulfilled',
      payload: wallet,
    });
    expect(nextState.wallet).toEqual(wallet);
    expect(nextState.status).toBe('succeeded');
    expect(nextState.error).toBeNull();
  });
}); 