import api from './api';

export async function getWallets(): Promise<string[]> {
  const response = await api.get<string[]>('/defi/wallets');
  return response.data;
}

export async function getWalletDetails(walletId: string): Promise<any> {
  const response = await api.get(`/defi/wallets/${walletId}`);
  return response.data;
}

export async function getWalletTransactions(walletId: string): Promise<any[]> {
  const response = await api.get(`/defi/wallets/${walletId}/transactions`);
  return response.data;
}
