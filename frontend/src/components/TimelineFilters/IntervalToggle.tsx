import React from 'react';

type Interval = 'daily' | 'weekly';

interface Props {
  value: Interval;
  onChange: (interval: Interval) => void;
}

export const IntervalToggle: React.FC<Props> = ({ value, onChange }) => (
  <label style={{ marginRight: '1rem' }}>
    Interval:
    <select
      value={value}
      onChange={e => onChange(e.target.value as Interval)}
      style={{ marginLeft: '0.5rem' }}
    >
      <option value="daily">Daily</option>
      <option value="weekly">Weekly</option>
    </select>
  </label>
);
