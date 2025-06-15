import React from 'react';
import { render, screen } from '@testing-library/react';
import { Home } from '../pages/Home/Home';

describe('Home Component', () => {
  it('renders welcome message', () => {
    render(<Home />);
    const titleElement = screen.getByText(/SmartWalletFX/i);
    const subtitleElement = screen.getByText(/Your Smart Crypto Portfolio Tracker/i);

    expect(titleElement).toBeInTheDocument();
    expect(subtitleElement).toBeInTheDocument();
  });
});
