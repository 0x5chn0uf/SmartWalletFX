import React from 'react';
import { render, screen } from '@testing-library/react';
import WalletListPage from '../../pages/WalletListPage';

describe('WalletListPage', () => {
  it('renders wallet list page', () => {
    render(<WalletListPage />);
    expect(screen.getByText(/wallet/i)).toBeInTheDocument();
  });
}); 