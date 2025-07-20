import api from './api';
import { validateApiResponse } from '../utils/validation';
import {
  WalletListSchema,
  WalletDetailsSchema,
  type WalletList,
  type WalletDetails,
  TransactionSchema,
  type Transaction,
} from '../schemas/wallet';

export async function getWallets(): Promise<WalletList> {
  const response = await api.get('/defi/wallets');
  return validateApiResponse(response, WalletListSchema);
}

export async function getWalletDetails(walletId: string): Promise<WalletDetails> {
  const response = await api.get(`/defi/wallets/${walletId}`);
  return validateApiResponse(response, WalletDetailsSchema);
}

export async function getWalletTransactions(walletId: string): Promise<Transaction[]> {
  const response = await api.get(`/defi/wallets/${walletId}/transactions`);
  return validateApiResponse(response, TransactionSchema.array());
}
