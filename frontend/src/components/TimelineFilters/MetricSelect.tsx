import React from 'react';

type Metric = 'collateral' | 'borrowings' | 'health_score';

interface Props {
  value: Metric;
  onChange: (metric: Metric) => void;
}

export const MetricSelect: React.FC<Props> = ({ value, onChange }) => (
  <label style={{ marginRight: '1rem' }}>
    Metric:
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as Metric)}
      style={{ marginLeft: '0.5rem' }}
    >
      <option value="collateral">Collateral</option>
      <option value="borrowings">Borrowings</option>
      <option value="health_score">Health Score</option>
    </select>
  </label>
); 