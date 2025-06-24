import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';

interface Wallet {
  id: string;
  name: string;
  address: string;
  balance: number;
  currency: string;
  lastUpdated: string;
}

interface WalletTableProps {
  wallets: Wallet[];
}

const WalletTable: React.FC<WalletTableProps> = ({ wallets }) => (
  <TableContainer component={Paper}>
    <Table>
      <TableHead>
        <TableRow>
          <TableCell>Name</TableCell>
          <TableCell>Address</TableCell>
          <TableCell align="right">Balance</TableCell>
          <TableCell>Last Updated</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {wallets.map((wallet) => (
          <TableRow key={wallet.id} hover>
            <TableCell>{wallet.name}</TableCell>
            <TableCell>{wallet.address}</TableCell>
            <TableCell align="right">${wallet.balance.toLocaleString()}</TableCell>
            <TableCell>{new Date(wallet.lastUpdated).toLocaleDateString()}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
);

export default WalletTable; 