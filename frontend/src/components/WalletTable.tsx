import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';

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

const WalletTable: React.FC<WalletTableProps> = ({ wallets }) => {
  const navigate = useNavigate();

  const handleRowClick = (walletId: string) => {
    navigate(`/wallets/${walletId}`);
  };

  return (
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
            <TableRow 
              key={wallet.id} 
              hover 
              onClick={() => handleRowClick(wallet.id)}
              sx={{ 
                cursor: 'pointer',
                '&:hover': { backgroundColor: 'action.hover' }
              }}
            >
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
};

export default WalletTable; 