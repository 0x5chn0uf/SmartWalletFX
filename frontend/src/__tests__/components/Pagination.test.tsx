import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Pagination from '../../components/Pagination';

describe('Pagination', () => {
  it('renders the correct number of pages', () => {
    render(
      <Pagination page={1} total={30} limit={10} onPageChange={() => {}} />
    );
    // Should render 3 pages (1, 2, 3) with accessible names
    expect(screen.getByRole('button', { name: 'page 1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go to page 2' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go to page 3' })).toBeInTheDocument();
  });

  it('calls onPageChange when a page is clicked', async () => {
    const onPageChange = jest.fn();
    render(
      <Pagination page={1} total={30} limit={10} onPageChange={onPageChange} />
    );
    await userEvent.click(screen.getByRole('button', { name: 'Go to page 2' }));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });
}); 