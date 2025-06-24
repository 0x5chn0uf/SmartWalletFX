import * as defi from '../../services/defi';
import apiClient from '../../services/api';

jest.mock('../../services/api');

describe('getTimeline', () => {
  it('should call apiClient.get and return data', async () => {
    const mockData = [{ date: '2024-06-18', balance: 100 }];
    (apiClient.get as jest.Mock).mockResolvedValue({ data: mockData });
    const result = await defi.getTimeline('0x123', { from_ts: 0, to_ts: 0 });
    expect(apiClient.get).toHaveBeenCalledWith('/defi/timeline/0x123?from_ts=0&to_ts=0');
    expect(result).toEqual(mockData);
  });
}); 