import React from 'react';
import { render, screen } from '@testing-library/react';
import WalletTable from '../../components/WalletTable';
import { MemoryRouter } from 'react-router-dom';

const mockWallets = [
  {
    id: '1',
    name: 'Main Wallet',
    address: '0x1234...5678',
    balance: 15000,
    currency: 'USD',
    lastUpdated: '2024-06-22T10:30:00Z'
  },
  {
    id: '2',
    name: 'Trading Wallet',
    address: '0x8765...4321',
    balance: 8500,
    currency: 'USD',
    lastUpdated: '2024-06-22T09:15:00Z'
  }
];

describe('WalletTable', () => {
  it('renders wallet data correctly', () => {
    render(
      <MemoryRouter>
        <WalletTable wallets={mockWallets} />
      </MemoryRouter>
    );
    
    expect(screen.getByText('Main Wallet')).toBeInTheDocument();
    expect(screen.getByText('Trading Wallet')).toBeInTheDocument();
    expect(screen.getByText('0x1234...5678')).toBeInTheDocument();
    expect(screen.getByText('$15,000')).toBeInTheDocument();
    expect(screen.getByText('$8,500')).toBeInTheDocument();
  });

  it('renders table headers', () => {
    render(
      <MemoryRouter>
        <WalletTable wallets={mockWallets} />
      </MemoryRouter>
    );
    
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Address')).toBeInTheDocument();
    expect(screen.getByText('Balance')).toBeInTheDocument();
    expect(screen.getByText('Last Updated')).toBeInTheDocument();
  });
}); 