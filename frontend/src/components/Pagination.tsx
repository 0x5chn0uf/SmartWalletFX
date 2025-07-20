import React from 'react';
import styled from '@emotion/styled';

const PaginationContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 2rem 0;
  gap: 0.5rem;
`;

const PageButton = styled.button<{ active?: boolean; disabled?: boolean }>`
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  background: ${props => (props.active ? '#3b82f6' : 'white')};
  color: ${props => (props.active ? 'white' : '#374151')};
  border-radius: 0.375rem;
  cursor: ${props => (props.disabled ? 'not-allowed' : 'pointer')};
  opacity: ${props => (props.disabled ? 0.5 : 1)};
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: ${props => (props.active ? '#2563eb' : '#f3f4f6')};
  }
`;

const PageInfo = styled.span`
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0 1rem;
`;

interface PaginationProps {
  page: number;
  total: number;
  limit: number;
  onPageChange: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({ page, total, limit, onPageChange }) => {
  const totalPages = Math.ceil(total / limit);

  if (totalPages <= 1) return null;

  const handlePrevious = () => {
    if (page > 1) onPageChange(page - 1);
  };

  const handleNext = () => {
    if (page < totalPages) onPageChange(page + 1);
  };

  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (page <= 3) {
        for (let i = 1; i <= 4; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      } else if (page >= totalPages - 2) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = page - 1; i <= page + 1; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      }
    }

    return pages;
  };

  return (
    <PaginationContainer>
      <PageButton onClick={handlePrevious} disabled={page === 1}>
        Previous
      </PageButton>

      {getPageNumbers().map((pageNum, index) =>
        typeof pageNum === 'number' ? (
          <PageButton key={pageNum} active={pageNum === page} onClick={() => onPageChange(pageNum)}>
            {pageNum}
          </PageButton>
        ) : (
          <PageInfo key={index}>{pageNum}</PageInfo>
        )
      )}

      <PageButton onClick={handleNext} disabled={page === totalPages}>
        Next
      </PageButton>
    </PaginationContainer>
  );
};

export default Pagination;
