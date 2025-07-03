import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Toast from '../../components/Toast';

describe('Toast', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  it('renders toast with message', () => {
    render(<Toast open={true} message="Test message" severity="success" onClose={mockOnClose} />);

    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(<Toast open={true} message="Test message" severity="error" onClose={mockOnClose} />);

    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('applies correct severity styling', () => {
    render(<Toast open={true} message="Test message" severity="warning" onClose={mockOnClose} />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('MuiAlert-standardWarning');
  });
});
