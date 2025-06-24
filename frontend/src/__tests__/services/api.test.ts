import apiClient from '../../services/api';

describe('apiClient', () => {
  it('should be defined and have get/post methods', () => {
    expect(apiClient).toBeDefined();
    expect(typeof apiClient.get).toBe('function');
    expect(typeof apiClient.post).toBe('function');
  });
}); 