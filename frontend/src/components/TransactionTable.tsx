import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from '@mui/material';
import { Transaction } from '../store/walletDetailSlice';

const formatCurrency = (amount: number, currency: string): string => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
};

interface TransactionTableProps {
  transactions: Transaction[];
}

const TransactionTable: React.FC<TransactionTableProps> = ({ transactions }) => (
  <TableContainer component={Paper} sx={{ mt: 3 }}>
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Date</TableCell>
          <TableCell>Type</TableCell>
          <TableCell align="right">Amount</TableCell>
          <TableCell align="right">Balance After</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {transactions.map(tx => (
          <TableRow key={tx.id} hover>
            <TableCell>{new Date(tx.date).toLocaleString()}</TableCell>
            <TableCell>
              <Chip
                label={tx.type}
                color={
                  tx.type === 'deposit' ? 'success' : tx.type === 'withdraw' ? 'error' : 'info'
                }
                size="small"
              />
            </TableCell>
            <TableCell align="right">{formatCurrency(tx.amount, tx.currency)}</TableCell>
            <TableCell align="right">{formatCurrency(tx.balanceAfter, tx.currency)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
);

export default TransactionTable;
