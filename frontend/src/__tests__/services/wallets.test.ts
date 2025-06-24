import * as wallets from '../../services/wallets';
import apiClient from '../../services/api';

jest.mock('../../services/api');

describe('getWallets', () => {
  it('should call apiClient.get and return data', async () => {
    const mockData = [{ id: '1', name: 'Wallet 1' }];
    (apiClient.get as jest.Mock).mockResolvedValue({ data: mockData });
    const result = await wallets.getWallets();
    expect(apiClient.get).toHaveBeenCalledWith('/defi/wallets');
    expect(result).toEqual(mockData);
  });
}); 