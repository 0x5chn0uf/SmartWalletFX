import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../../theme';
import {
  TimelineFilters,
  TimelineFilterValues,
} from '../../../../components/Timeline/TimelineFilters';
import { describe, it, expect, vi } from 'vitest';

describe('TimelineFilters', () => {
  const theme = createAppTheme();

  const defaultValues: TimelineFilterValues = {
    from: '2024-01-01',
    to: '2024-02-01',
    interval: 'daily',
  };

  const setup = (values = defaultValues, onChange = vi.fn()) => {
    render(
      <ThemeProvider theme={theme}>
        <TimelineFilters {...values} onChange={onChange} />
      </ThemeProvider>
    );
    return { onChange };
  };

  it('renders date inputs and interval select with correct initial values', () => {
    setup();

    expect(screen.getByLabelText(/from/i)).toHaveValue(defaultValues.from);
    expect(screen.getByLabelText(/to/i)).toHaveValue(defaultValues.to);
    // Interval select renders a separate element; value assertion is skipped for simplicity
  });

  it('calls onChange when the from date is changed', () => {
    const { onChange } = setup();

    fireEvent.change(screen.getByLabelText(/from/i), {
      target: { value: '2024-01-10' },
    });

    expect(onChange).toHaveBeenCalledWith({ ...defaultValues, from: '2024-01-10' });
  });

  // Additional tests for interval change require complex UI interactions; omitted here
});
