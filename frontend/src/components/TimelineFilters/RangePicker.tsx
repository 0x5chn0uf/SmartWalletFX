import React from 'react';

interface Props {
  from: string;
  to: string;
  onChange: (from: string, to: string) => void;
}

export const RangePicker: React.FC<Props> = ({ from, to, onChange }) => (
  <span style={{ marginRight: '1rem' }}>
    From: <input type="date" value={from} onChange={e => onChange(e.target.value, to)} /> To:{' '}
    <input type="date" value={to} onChange={e => onChange(from, e.target.value)} />
  </span>
);
