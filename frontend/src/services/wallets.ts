import { api } from './api';

export async function getWallets(): Promise<string[]> {
  const response = await api.get<string[]>('/defi/wallets');
  return response.data;
}
