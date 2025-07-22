import { z } from 'zod';

// Wallet Balance Schema
export const WalletBalanceSchema = z.object({
  address: z.string(),
  balance: z.string(),
  token: z.string(),
});

// Chart Data Schema
export const ChartDataSchema = z.object({
  timestamp: z.number(),
  value: z.number(),
});

// Transaction Schema
export const TransactionSchema = z.object({
  id: z.string(),
  hash: z.string(),
  from: z.string(),
  to: z.string(),
  value: z.string(),
  timestamp: z.number(),
  status: z.enum(['pending', 'confirmed', 'failed']),
  gas_used: z.string().optional(),
  gas_price: z.string().optional(),
});

// Wallet Details Schema
export const WalletDetailsSchema = z.object({
  address: z.string(),
  name: z.string().optional(),
  balance: z.string(),
  token: z.string(),
  usd_value: z.number().optional(),
  portfolio_percentage: z.number().optional(),
  transactions: z.array(TransactionSchema).optional(),
  chart_data: z.array(ChartDataSchema).optional(),
});

// Wallet List Response Schema (array of wallet addresses)
export const WalletListSchema = z.array(z.string());

// Portfolio Metrics Schema
export const PortfolioMetricsSchema = z.object({
  total_value_usd: z.number(),
  total_change_24h: z.number(),
  total_change_24h_percent: z.number(),
  asset_breakdown: z.array(
    z.object({
      symbol: z.string(),
      value_usd: z.number(),
      percentage: z.number(),
    })
  ),
});

// Type exports for TypeScript
export type WalletBalance = z.infer<typeof WalletBalanceSchema>;
export type ChartData = z.infer<typeof ChartDataSchema>;
export type Transaction = z.infer<typeof TransactionSchema>;
export type WalletDetails = z.infer<typeof WalletDetailsSchema>;
export type WalletList = z.infer<typeof WalletListSchema>;
export type PortfolioMetrics = z.infer<typeof PortfolioMetricsSchema>;
