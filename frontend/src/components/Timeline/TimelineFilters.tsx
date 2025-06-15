import React from 'react';
import { Box, TextField, MenuItem } from '@mui/material';

export type TimelineFilterValues = {
  from: string; // YYYY-MM-DD
  to: string; // YYYY-MM-DD
  interval: 'none' | 'daily' | 'weekly';
};

interface Props extends TimelineFilterValues {
  onChange: (v: TimelineFilterValues) => void;
}

export const TimelineFilters: React.FC<Props> = ({ from, to, interval, onChange }) => {
  return (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
      <TextField
        label="From"
        type="date"
        value={from}
        onChange={e => onChange({ from: e.target.value, to, interval })}
        InputLabelProps={{ shrink: true }}
        size="small"
      />
      <TextField
        label="To"
        type="date"
        value={to}
        onChange={e => onChange({ from, to: e.target.value, interval })}
        InputLabelProps={{ shrink: true }}
        size="small"
      />
      <TextField
        select
        label="Interval"
        value={interval}
        onChange={e =>
          onChange({ from, to, interval: e.target.value as TimelineFilterValues['interval'] })
        }
        size="small"
      >
        {['none', 'daily', 'weekly'].map(opt => (
          <MenuItem key={opt} value={opt}>
            {opt}
          </MenuItem>
        ))}
      </TextField>
    </Box>
  );
};
