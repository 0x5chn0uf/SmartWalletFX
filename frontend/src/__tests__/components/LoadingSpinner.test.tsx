import React from 'react';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../../components/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders a progress indicator', () => {
    render(<LoadingSpinner />);
    // MUI CircularProgress uses role="progressbar"
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
}); 