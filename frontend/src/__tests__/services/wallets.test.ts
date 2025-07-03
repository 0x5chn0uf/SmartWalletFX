import * as wallets from '../../services/wallets';
import apiClient from '../../services/api';
import { vi } from 'vitest';

vi.mock('../../services/api');

describe('getWallets', () => {
  it('should call apiClient.get and return data', async () => {
    const mockData = [{ id: '1', name: 'Wallet 1' }];
    (apiClient.get as vi.Mock).mockResolvedValue({ data: mockData });
    const result = await wallets.getWallets();
    expect(apiClient.get).toHaveBeenCalledWith('/defi/wallets');
    expect(result).toEqual(mockData);
  });
});

describe('getWalletDetails', () => {
  it('requests wallet details by id', async () => {
    (apiClient.get as vi.Mock).mockResolvedValue({ data: { id: '2' } });
    const result = await wallets.getWalletDetails('2');
    expect(apiClient.get).toHaveBeenCalledWith('/defi/wallets/2');
    expect(result).toEqual({ id: '2' });
  });
});

describe('getWalletTransactions', () => {
  it('requests wallet transactions by id', async () => {
    (apiClient.get as vi.Mock).mockResolvedValue({ data: [1, 2, 3] });
    const result = await wallets.getWalletTransactions('3');
    expect(apiClient.get).toHaveBeenCalledWith('/defi/wallets/3/transactions');
    expect(result).toEqual([1, 2, 3]);
  });
});
