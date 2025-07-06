import React from 'react';
import { Skeleton } from '@mui/material';

/**
 * A placeholder skeleton for charts shown while data is loading.
 */
const ChartSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div
    className={`bg-gray-200 dark:bg-gray-700 rounded-md h-64 flex items-center justify-center ${className}`}
  >
    {/* Spread a few skeleton bars to simulate a chart */}
    <div className="w-full px-4">
      {[...Array(5)].map((_, idx) => (
        <Skeleton
          key={idx}
          variant="rectangular"
          height={16 + idx * 12}
          animation="wave"
          style={{ marginBottom: 8 }}
        />
      ))}
    </div>
  </div>
);

export default ChartSkeleton;
