import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AxiosResponse } from 'axios';
import { getWallets, getWalletDetails, getWalletTransactions } from '../../services/wallets';
import api from '../../services/api';
import { ValidationError } from '../../utils/validation';

// Mock the API client
vi.mock('../../services/api');
const mockedApi = vi.mocked(api);

describe('Wallet Services with Validation Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockResponse = (data: any, status = 200): AxiosResponse => ({
    data,
    status,
    statusText: 'OK',
    headers: {},
    config: { url: '/api/test' } as any,
  });

  describe('getWallets', () => {
    it('should return validated wallet list when API returns valid data', async () => {
      const validWalletList = [
        '0x1234567890abcdef1234567890abcdef12345678',
        '0xabcdef1234567890abcdef1234567890abcdef12',
      ];

      mockedApi.get.mockResolvedValue(mockResponse(validWalletList));

      const result = await getWallets();
      expect(result).toEqual(validWalletList);
      expect(mockedApi.get).toHaveBeenCalledWith('/defi/wallets');
    });

    it('should throw ValidationError when API returns invalid data', async () => {
      const invalidWalletList = [
        '0x1234567890abcdef1234567890abcdef12345678',
        123, // invalid - should be string
      ];

      mockedApi.get.mockResolvedValue(mockResponse(invalidWalletList));

      await expect(getWallets()).rejects.toThrow(ValidationError);
    });

    it('should handle empty wallet list', async () => {
      const emptyWalletList: string[] = [];

      mockedApi.get.mockResolvedValue(mockResponse(emptyWalletList));

      const result = await getWallets();
      expect(result).toEqual(emptyWalletList);
    });
  });

  describe('getWalletDetails', () => {
    it('should return validated wallet details when API returns valid data', async () => {
      const validWalletDetails = {
        address: '0x1234567890abcdef1234567890abcdef12345678',
        name: 'My Wallet',
        balance: '1000.50',
        token: 'ETH',
        usd_value: 2500.75,
        portfolio_percentage: 45.5,
      };

      mockedApi.get.mockResolvedValue(mockResponse(validWalletDetails));

      const result = await getWalletDetails('0x1234567890abcdef1234567890abcdef12345678');
      expect(result).toEqual(validWalletDetails);
      expect(mockedApi.get).toHaveBeenCalledWith(
        '/defi/wallets/0x1234567890abcdef1234567890abcdef12345678'
      );
    });

    it('should return validated wallet details with minimal required fields', async () => {
      const minimalWalletDetails = {
        address: '0x1234567890abcdef1234567890abcdef12345678',
        balance: '1000.50',
        token: 'ETH',
      };

      mockedApi.get.mockResolvedValue(mockResponse(minimalWalletDetails));

      const result = await getWalletDetails('0x1234567890abcdef1234567890abcdef12345678');
      expect(result).toEqual(minimalWalletDetails);
    });

    it('should throw ValidationError when API returns invalid wallet details', async () => {
      const invalidWalletDetails = {
        address: '0x1234567890abcdef1234567890abcdef12345678',
        // missing required balance and token fields
      };

      mockedApi.get.mockResolvedValue(mockResponse(invalidWalletDetails));

      await expect(getWalletDetails('0x1234567890abcdef1234567890abcdef12345678')).rejects.toThrow(
        ValidationError
      );
    });
  });

  describe('getWalletTransactions', () => {
    it('should return validated transactions when API returns valid data', async () => {
      const validTransactions = [
        {
          id: 'tx-123',
          hash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
          from: '0x1111111111111111111111111111111111111111',
          to: '0x2222222222222222222222222222222222222222',
          value: '1000000000000000000',
          timestamp: 1640995200000,
          status: 'confirmed' as const,
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
          status: 'pending' as const,
        },
      ];

      mockedApi.get.mockResolvedValue(mockResponse(validTransactions));

      const result = await getWalletTransactions('0x1234567890abcdef1234567890abcdef12345678');
      expect(result).toEqual(validTransactions);
      expect(mockedApi.get).toHaveBeenCalledWith(
        '/defi/wallets/0x1234567890abcdef1234567890abcdef12345678/transactions'
      );
    });

    it('should handle empty transactions array', async () => {
      const emptyTransactions: any[] = [];

      mockedApi.get.mockResolvedValue(mockResponse(emptyTransactions));

      const result = await getWalletTransactions('0x1234567890abcdef1234567890abcdef12345678');
      expect(result).toEqual(emptyTransactions);
    });

    it('should throw ValidationError when API returns invalid transaction data', async () => {
      const invalidTransactions = [
        {
          id: 'tx-123',
          hash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
          from: '0x1111111111111111111111111111111111111111',
          to: '0x2222222222222222222222222222222222222222',
          value: '1000000000000000000',
          timestamp: 1640995200000,
          status: 'invalid-status', // invalid status
        },
      ];

      mockedApi.get.mockResolvedValue(mockResponse(invalidTransactions));

      await expect(
        getWalletTransactions('0x1234567890abcdef1234567890abcdef12345678')
      ).rejects.toThrow(ValidationError);
    });
  });

  describe('Error handling and logging', () => {
    it('should log validation errors with request context', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const invalidData = ['invalid', 123]; // should be array of strings
      mockedApi.get.mockResolvedValue(mockResponse(invalidData));

      try {
        await getWallets();
      } catch (error) {
        expect(error).toBeInstanceOf(ValidationError);
      }

      expect(consoleSpy).toHaveBeenCalledWith(
        'API Response validation failed:',
        expect.objectContaining({
          url: '/api/test',
          status: 200,
          receivedData: invalidData,
        })
      );

      consoleSpy.mockRestore();
    });
  });
});
