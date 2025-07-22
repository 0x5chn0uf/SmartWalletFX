// Re-export validated types from schemas
export type { UserProfile, AuthError, TokenResponse, ApiError } from '../schemas/api';

export type {
  WalletBalance,
  WalletDetails,
  WalletList,
  Transaction,
  ChartData,
  PortfolioMetrics,
} from '../schemas/wallet';

// Legacy API Response Types (consider migrating to zod schemas)
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

// User Settings
export interface UserSettings {
  theme: 'light' | 'dark';
  currency: string;
  timeframe: string;
}
