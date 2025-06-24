import React from 'react';

const ChartPlaceholder: React.FC<{ className?: string }> = ({ className }) => (
  <div
    className={`flex items-center justify-center bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-300 rounded-md h-64 ${className}`}
  >
    <span>Chart coming soon...</span>
  </div>
);

export default ChartPlaceholder; 