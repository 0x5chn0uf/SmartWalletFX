import React from 'react';
import { render, screen } from '@testing-library/react';
import ChartPlaceholder from '../../components/ChartPlaceholder';

describe('ChartPlaceholder', () => {
  it('renders placeholder text', () => {
    render(<ChartPlaceholder />);
    expect(screen.getByText('Chart coming soon...')).toBeInTheDocument();
  });
});
