import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';

interface SummaryCardProps {
  title: string;
  value: string | number;
  className?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ title, value, className = '' }) => (
  <Card className={`shadow-md ${className}`}>
    <CardContent>
      <Typography variant="subtitle2" color="textSecondary" gutterBottom>
        {title}
      </Typography>
      <Typography variant="h5" component="p">
        {value}
      </Typography>
    </CardContent>
  </Card>
);

export default SummaryCard;
