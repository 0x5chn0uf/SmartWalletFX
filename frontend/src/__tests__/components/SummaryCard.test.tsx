import React from 'react';
import { render, screen } from '@testing-library/react';
import SummaryCard from '../../components/SummaryCard';

describe('SummaryCard', () => {
  it('renders the title and value', () => {
    render(<SummaryCard title="Total Balance" value={1000} />);
    expect(screen.getByText('Total Balance')).toBeInTheDocument();
    expect(screen.getByText('1000')).toBeInTheDocument();
  });
}); 