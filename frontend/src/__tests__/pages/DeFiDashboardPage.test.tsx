import React from 'react';
import { render, screen } from '@testing-library/react';
import DeFiDashboardPage from '../../pages/DeFiDashboardPage';

describe('DeFiDashboardPage', () => {
  it('renders static dashboard sections', () => {
    render(<DeFiDashboardPage />);
    expect(screen.getByText(/Total Value of Wallet/i)).toBeInTheDocument();
    expect(screen.getByText(/Performance Timeline/i)).toBeInTheDocument();
  });
});
