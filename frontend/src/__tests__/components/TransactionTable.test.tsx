import React from 'react';
import { render, screen } from '@testing-library/react';
import TransactionTable from '../../components/TransactionTable';
import { Transaction } from '../../store/walletDetailSlice';

describe('TransactionTable', () => {
  it('renders transaction rows', () => {
    const transactions: Transaction[] = [
      {
        id: '1',
        date: '2024-06-18T12:00:00Z',
        type: 'deposit',
        amount: 0.5,
        currency: 'USD',
        balanceAfter: 100.5,
      },
      {
        id: '2',
        date: '2024-06-19T12:00:00Z',
        type: 'withdraw',
        amount: 1.2,
        currency: 'USD',
        balanceAfter: 99.3,
      },
    ];
    render(<TransactionTable transactions={transactions} />);
    expect(screen.getByText('deposit')).toBeInTheDocument();
    expect(screen.getByText('withdraw')).toBeInTheDocument();
  });
}); 