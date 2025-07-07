// @ts-nocheck
import React from 'react';
import { render, screen } from '@testing-library/react';
import HeroSection from '../../components/home/HeroSection';

describe('HeroSection', () => {
  it('renders headline and buttons', () => {
    render(<HeroSection />);
    expect(screen.getByText('Your Smart Wallet for Algorithmic Trading')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Launch App/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Connect Wallet/i })).toBeInTheDocument();
  });
});
