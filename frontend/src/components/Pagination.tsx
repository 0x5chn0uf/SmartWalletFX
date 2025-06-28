import React from 'react';
import { Pagination as MuiPagination, Box } from '@mui/material';

interface PaginationProps {
  page: number;
  total: number;
  limit: number;
  onPageChange: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({ page, total, limit, onPageChange }) => {
  const totalPages = Math.ceil(total / limit);

  return (
    <Box display="flex" justifyContent="center" mt={2}>
      <MuiPagination
        count={totalPages}
        page={page}
        onChange={(_, newPage) => onPageChange(newPage)}
        color="primary"
      />
    </Box>
  );
};

export default Pagination;
