import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Pagination from '../../components/Pagination';

describe('Pagination', () => {
  it('renders the correct number of pages', () => {
    render(<Pagination page={1} total={30} limit={10} onPageChange={() => {}} />);
    // Should render 3 pages (1, 2, 3) with accessible names
    expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '2' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '3' })).toBeInTheDocument();
  });

  it('calls onPageChange when a page is clicked', async () => {
    const onPageChange = vi.fn();
    render(<Pagination page={1} total={30} limit={10} onPageChange={onPageChange} />);
    await userEvent.click(screen.getByRole('button', { name: '2' }));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('should render pagination controls with buttons', () => {
    render(<Pagination page={2} total={50} limit={10} onPageChange={() => {}} />);

    // Should render Previous, Next, and page number buttons
    expect(screen.getByRole('button', { name: 'Previous' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Next' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '2' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '3' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '4' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '5' })).toBeInTheDocument();
  });

  it('disables Previous button on first page', () => {
    render(<Pagination page={1} total={30} limit={10} onPageChange={() => {}} />);
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled();
  });

  it('disables Next button on last page', () => {
    render(<Pagination page={3} total={30} limit={10} onPageChange={() => {}} />);
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled();
  });

  it('calls onPageChange when Previous button is clicked', async () => {
    const onPageChange = vi.fn();
    render(<Pagination page={2} total={30} limit={10} onPageChange={onPageChange} />);
    await userEvent.click(screen.getByRole('button', { name: 'Previous' }));
    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it('calls onPageChange when Next button is clicked', async () => {
    const onPageChange = vi.fn();
    render(<Pagination page={1} total={30} limit={10} onPageChange={onPageChange} />);
    await userEvent.click(screen.getByRole('button', { name: 'Next' }));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});
