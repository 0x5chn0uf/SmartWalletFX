import React from 'react';
import { render, screen } from '@testing-library/react';
import HomePage from '../../pages/HomePage';

describe('HomePage', () => {
  it('renders home page content', () => {
    render(<HomePage />);
    expect(screen.getByText('Your Smart Wallet for Algorithmic Trading')).toBeInTheDocument();
  });
});
