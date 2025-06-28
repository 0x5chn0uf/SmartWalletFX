import React from 'react';
import { Box, Paper, Typography, IconButton, Tooltip } from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

// Placeholder for a whale's tail icon
const WhaleIcon = () => (
  <svg
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{ marginRight: '8px' }}
  >
    <path
      d="M16.74,7.82C16.59,7.37 16.21,7 15.77,7H14V5C14,3.9 13.1,3 12,3C10.9,3 10,3.9 10,5V7H8.23C7.79,7 7.41,7.37 7.26,7.82L5,14V19C5,20.1 5.9,21 7,21H17C18.1,21 19,20.1 19,19V14L16.74,7.82ZM12,18C11.17,18 10.5,17.33 10.5,16.5C10.5,15.67 11.17,15 12,15C12.83,15 13.5,15.67 13.5,16.5C13.5,17.33 12.83,18 12,18Z"
      fill="currentColor"
    />
  </svg>
);

export const SmartTraderMoves: React.FC = () => {
  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        mt: 4,
        backgroundColor: 'rgba(25, 118, 210, 0.08)', // Subtle blue background
        border: '1px solid rgba(25, 118, 210, 0.12)',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <WhaleIcon />
        <Typography variant="h6" component="h3" sx={{ flexGrow: 1 }}>
          Smart Trader Moves
        </Typography>
        <Tooltip
          title="This section highlights recent, significant transactions from highly successful wallets, often referred to as 'smart money' or 'whales'."
          arrow
        >
          <IconButton size="small">
            <InfoOutlinedIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      <Typography variant="body2" color="text.secondary">
        Placeholder for recent transactions from top-performing wallets. This feature is coming
        soon.
      </Typography>
      {/* Future implementation will include a list of transactions */}
    </Paper>
  );
};
