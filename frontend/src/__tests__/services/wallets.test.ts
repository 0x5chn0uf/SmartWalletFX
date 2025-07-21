import * as wallets from '../../services/wallets';
import apiClient from '../../services/api';
import { vi } from 'vitest';

vi.mock('../../services/api');

describe('getWallets', () => {
  it('should call apiClient.get and return data', async () => {
    // WalletListSchema expects array of strings (wallet addresses)
    const mockData = [
      '0x1234567890abcdef1234567890abcdef12345678',
      '0xabcdef1234567890abcdef1234567890abcdef12',
    ];
    (apiClient.get as vi.Mock).mockResolvedValue({ data: mockData });
    const result = await wallets.getWallets();
    expect(apiClient.get).toHaveBeenCalledWith('/defi/wallets');
    expect(result).toEqual(mockData);
  });
});

describe('getWalletDetails', () => {
  it('requests wallet details by id', async () => {
    // WalletDetailsSchema expects address, balance, and token as required fields
    const mockData = {
      address: '0x1234567890abcdef1234567890abcdef12345678',
      name: 'My Test Wallet',
      balance: '1000.50',
      token: 'ETH',
      usd_value: 2500.75,
      portfolio_percentage: 45.5,
    };
    (apiClient.get as vi.Mock).mockResolvedValue({ data: mockData });
    const result = await wallets.getWalletDetails('2');
    expect(apiClient.get).toHaveBeenCalledWith('/defi/wallets/2');
    expect(result).toEqual(mockData);
  });
});

describe('getWalletTransactions', () => {
  it('requests wallet transactions by id', async () => {
    // TransactionSchema expects transaction objects with specific structure
    const mockData = [
      {
        id: 'tx-123',
        hash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
        from: '0x1111111111111111111111111111111111111111',
        to: '0x2222222222222222222222222222222222222222',
        value: '1000000000000000000',
        timestamp: 1640995200000,
        status: 'confirmed',
        gas_used: '21000',
        gas_price: '20000000000',
      },
      {
        id: 'tx-456',
        hash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        from: '0x3333333333333333333333333333333333333333',
        to: '0x4444444444444444444444444444444444444444',
        value: '500000000000000000',
        timestamp: 1640995260000,
        status: 'pending',
      },
    ];
    (apiClient.get as vi.Mock).mockResolvedValue({ data: mockData });
    const result = await wallets.getWalletTransactions('3');
    expect(apiClient.get).toHaveBeenCalledWith('/defi/wallets/3/transactions');
    expect(result).toEqual(mockData);
  });
});
