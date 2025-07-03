import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { RangePicker } from '../../../../components/TimelineFilters/RangePicker';
import { describe, it, expect, vi } from 'vitest';

describe('RangePicker', () => {
  const setup = (from = '2024-01-01', to = '2024-02-01', onChange = vi.fn()) => {
    const utils = render(<RangePicker from={from} to={to} onChange={onChange} />);
    return { onChange, ...utils };
  };

  it('renders inputs with initial values', () => {
    const { container } = setup();
    const inputs = container.querySelectorAll('input');
    expect(inputs[0]).toHaveValue('2024-01-01');
    expect(inputs[1]).toHaveValue('2024-02-01');
  });

  it('calls onChange with updated from date', () => {
    const { onChange, container } = setup();
    const inputs = container.querySelectorAll('input');
    fireEvent.change(inputs[0], { target: { value: '2024-01-15' } });
    expect(onChange).toHaveBeenCalledWith('2024-01-15', '2024-02-01');
  });

  it('calls onChange with updated to date', () => {
    const { onChange, container } = setup();
    const inputs = container.querySelectorAll('input');
    fireEvent.change(inputs[1], { target: { value: '2024-02-15' } });
    expect(onChange).toHaveBeenCalledWith('2024-01-01', '2024-02-15');
  });
});
