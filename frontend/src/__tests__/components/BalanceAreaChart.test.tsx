import React from 'react';
import { render } from '@testing-library/react';
import BalanceAreaChart from '../../components/BalanceAreaChart';

describe('BalanceAreaChart', () => {
  it('renders without crashing', () => {
    render(<BalanceAreaChart data={[]} />);
    // No assertion: just check render does not throw
  });
}); 