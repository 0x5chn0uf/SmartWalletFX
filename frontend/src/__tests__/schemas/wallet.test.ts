import { describe, it, expect } from 'vitest';
import {
  WalletBalanceSchema,
  ChartDataSchema,
  TransactionSchema,
  WalletDetailsSchema,
  WalletListSchema,
  PortfolioMetricsSchema,
} from '../../schemas/wallet';

describe('Wallet Schemas', () => {
  describe('WalletBalanceSchema', () => {
    it('should validate a valid wallet balance', () => {
      const validBalance = {
        address: '0x1234567890abcdef1234567890abcdef12345678',
        balance: '1000.50',
        token: 'ETH',
      };

      const result = WalletBalanceSchema.safeParse(validBalance);
      expect(result.success).toBe(true);
    });

    it('should reject missing required fields', () => {
      const invalidBalance = {
        address: '0x1234567890abcdef1234567890abcdef12345678',
        // missing balance and token
      };

      const result = WalletBalanceSchema.safeParse(invalidBalance);
      expect(result.success).toBe(false);
    });
  });

  describe('ChartDataSchema', () => {
    it('should validate valid chart data', () => {
      const validChartData = {
        timestamp: 1640995200000,
        value: 42.5,
      };

      const result = ChartDataSchema.safeParse(validChartData);
      expect(result.success).toBe(true);
    });

    it('should reject non-numeric values', () => {
      const invalidChartData = {
        timestamp: '2022-01-01',
        value: 'invalid',
      };

      const result = ChartDataSchema.safeParse(invalidChartData);
      expect(result.success).toBe(false);
    });
  });

  describe('TransactionSchema', () => {
    it('should validate a complete transaction', () => {
      const validTransaction = {
        id: 'tx-123',
        hash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
        from: '0x1111111111111111111111111111111111111111',
        to: '0x2222222222222222222222222222222222222222',
        value: '1000000000000000000',
        timestamp: 1640995200000,
        status: 'confirmed' as const,
        gas_used: '21000',
        gas_price: '20000000000',
      };

      const result = TransactionSchema.safeParse(validTransaction);
      expect(result.success).toBe(true);
    });

    it('should validate transaction without optional fields', () => {
      const validTransaction = {
        id: 'tx-123',
        hash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
        from: '0x1111111111111111111111111111111111111111',
        to: '0x2222222222222222222222222222222222222222',
        value: '1000000000000000000',
        timestamp: 1640995200000,
        status: 'pending' as const,
      };

      const result = TransactionSchema.safeParse(validTransaction);
      expect(result.success).toBe(true);
    });

    it('should reject invalid status', () => {
      const invalidTransaction = {
        id: 'tx-123',
        hash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
        from: '0x1111111111111111111111111111111111111111',
        to: '0x2222222222222222222222222222222222222222',
        value: '1000000000000000000',
        timestamp: 1640995200000,
        status: 'invalid-status',
      };

      const result = TransactionSchema.safeParse(invalidTransaction);
      expect(result.success).toBe(false);
    });
  });

  describe('WalletDetailsSchema', () => {
    it('should validate complete wallet details', () => {
      const validWalletDetails = {
        address: '0x1234567890abcdef1234567890abcdef12345678',
        name: 'My Main Wallet',
        balance: '1000.50',
        token: 'ETH',
        usd_value: 2500.75,
        portfolio_percentage: 45.5,
        transactions: [
          {
            id: 'tx-123',
            hash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
            from: '0x1111111111111111111111111111111111111111',
            to: '0x2222222222222222222222222222222222222222',
            value: '1000000000000000000',
            timestamp: 1640995200000,
            status: 'confirmed' as const,
          },
        ],
        chart_data: [{ timestamp: 1640995200000, value: 42.5 }],
      };

      const result = WalletDetailsSchema.safeParse(validWalletDetails);
      expect(result.success).toBe(true);
    });

    it('should validate minimal wallet details', () => {
      const minimalWalletDetails = {
        address: '0x1234567890abcdef1234567890abcdef12345678',
        balance: '1000.50',
        token: 'ETH',
      };

      const result = WalletDetailsSchema.safeParse(minimalWalletDetails);
      expect(result.success).toBe(true);
    });
  });

  describe('WalletListSchema', () => {
    it('should validate array of wallet addresses', () => {
      const validWalletList = [
        '0x1234567890abcdef1234567890abcdef12345678',
        '0xabcdef1234567890abcdef1234567890abcdef12',
        '0x9876543210fedcba9876543210fedcba98765432',
      ];

      const result = WalletListSchema.safeParse(validWalletList);
      expect(result.success).toBe(true);
    });

    it('should validate empty wallet list', () => {
      const emptyWalletList: string[] = [];

      const result = WalletListSchema.safeParse(emptyWalletList);
      expect(result.success).toBe(true);
    });

    it('should reject non-string elements', () => {
      const invalidWalletList = [
        '0x1234567890abcdef1234567890abcdef12345678',
        123, // invalid
      ];

      const result = WalletListSchema.safeParse(invalidWalletList);
      expect(result.success).toBe(false);
    });
  });

  describe('PortfolioMetricsSchema', () => {
    it('should validate complete portfolio metrics', () => {
      const validMetrics = {
        total_value_usd: 10000.5,
        total_change_24h: 250.75,
        total_change_24h_percent: 2.57,
        asset_breakdown: [
          {
            symbol: 'ETH',
            value_usd: 5000.25,
            percentage: 50.0,
          },
          {
            symbol: 'BTC',
            value_usd: 3000.15,
            percentage: 30.0,
          },
          {
            symbol: 'USDC',
            value_usd: 2000.1,
            percentage: 20.0,
          },
        ],
      };

      const result = PortfolioMetricsSchema.safeParse(validMetrics);
      expect(result.success).toBe(true);
    });

    it('should validate portfolio metrics with empty asset breakdown', () => {
      const validMetrics = {
        total_value_usd: 0,
        total_change_24h: 0,
        total_change_24h_percent: 0,
        asset_breakdown: [],
      };

      const result = PortfolioMetricsSchema.safeParse(validMetrics);
      expect(result.success).toBe(true);
    });
  });
});
