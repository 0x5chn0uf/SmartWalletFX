import * as defi from '../../services/defi';
import apiClient from '../../services/api';
import { vi } from 'vitest';

vi.mock('../../services/api');

describe('getTimeline', () => {
  it('should call apiClient.get and return data', async () => {
    const mockData = [{ date: '2024-06-18', balance: 100 }];
    (apiClient.get as vi.Mock).mockResolvedValue({ data: mockData });
    const result = await defi.getTimeline('0x123', { from_ts: 0, to_ts: 0 });
    expect(apiClient.get).toHaveBeenCalledWith('/defi/timeline/0x123?from_ts=0&to_ts=0');
    expect(result).toEqual(mockData);
  });
});

describe('getDefiKPI', () => {
  it('should call api.get and return data', async () => {
    const mockData = {
      tvl: 1000000,
      apy: 7.5,
      updated_at: '2024-06-18T00:00:00Z',
      protocols: [
        { name: 'Aave', tvl: 500000, apy: 6.2, positions: 10 },
        { name: 'Compound', tvl: 500000, apy: 8.8, positions: 5 },
      ],
    };
    (apiClient.get as vi.Mock).mockResolvedValue({ data: mockData });
    const result = await defi.getDefiKPI();
    expect(apiClient.get).toHaveBeenCalledWith('/defi/portfolio/kpi');
    expect(result).toEqual(mockData);
  });
});

describe('getProtocolBreakdown', () => {
  it('should call api.get and return data', async () => {
    const mockData = [
      { name: 'Aave', tvl: 500000, apy: 6.2, positions: 10 },
      { name: 'Compound', tvl: 500000, apy: 8.8, positions: 5 },
    ];
    (apiClient.get as vi.Mock).mockResolvedValue({ data: mockData });
    const result = await defi.getProtocolBreakdown();
    expect(apiClient.get).toHaveBeenCalledWith('/defi/portfolio/protocols');
    expect(result).toEqual(mockData);
  });
});
