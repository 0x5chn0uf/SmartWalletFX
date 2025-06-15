// API Response Types
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

// Wallet Types
export interface WalletBalance {
  address: string;
  balance: string;
  token: string;
}

// Chart Types
export interface ChartData {
  timestamp: number;
  value: number;
}

// User Settings
export interface UserSettings {
  theme: 'light' | 'dark';
  currency: string;
  timeframe: string;
}
