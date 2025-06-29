import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';

interface SummaryCardProps {
  title: string;
  value: string | number;
  /**
   * Displays a skeleton loader instead of the value when true.
   */
  loading?: boolean;
  /**
   * Optional icon to show above the value.
   */
  icon?: React.ReactNode;
  className?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  value,
  loading = false,
  icon,
  className = '',
}) => (
  <Card className={`shadow-md ${className}`}>
    <CardContent className="flex flex-col items-center p-4">
      <div className="flex items-center mb-2">
        {icon && <div className="text-3xl text-indigo-500 mr-2">{icon}</div>}
        <Typography variant="subtitle2" color="textSecondary">
          {title}
        </Typography>
      </div>
      {loading ? (
        <div className="w-20">
          <div className="animate-pulse h-8 bg-gray-300 rounded" />
        </div>
      ) : (
        <Typography variant="h4" component="p" className="font-bold">
          {value}
        </Typography>
      )}
    </CardContent>
  </Card>
);

export default SummaryCard;
