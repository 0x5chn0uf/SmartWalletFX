import { http, HttpResponse } from 'msw';

const API_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000';

const handlers = [
  http.get(`${API_URL}/timeline`, () => {
    return HttpResponse.json({ data: [] });
  }),
  http.get(`${API_URL}/dashboard/overview`, () => {
    return HttpResponse.json({
      totalWallets: 12,
      totalBalance: 46230,
      chart: [
        { date: '2024-06-18', balance: 42000 },
        { date: '2024-06-19', balance: 43000 },
        { date: '2024-06-20', balance: 44000 },
        { date: '2024-06-21', balance: 44500 },
        { date: '2024-06-22', balance: 46230 },
      ],
      portfolioDistribution: [
        { id: 'btc', name: 'BTC', balance: 20000 },
        { id: 'eth', name: 'ETH', balance: 15000 },
        { id: 'usdc', name: 'USDC', balance: 5000 },
        { id: 'bnb', name: 'BNB', balance: 3000 },
        { id: 'sol', name: 'SOL', balance: 1230 },
      ],
    });
  }),
  http.get(`${API_URL}/wallets`, ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const search = url.searchParams.get('search') || '';

    const mockWallets = [
      {
        id: '1',
        name: 'Main Wallet (ETH)',
        address: '0x1234...5678',
        balance: 15000,
        currency: 'USD',
        lastUpdated: '2024-06-22T10:30:00Z',
      },
      {
        id: '2',
        name: 'Trading Wallet (BTC)',
        address: '0x8765...4321',
        balance: 8500,
        currency: 'USD',
        lastUpdated: '2024-06-22T09:15:00Z',
      },
      {
        id: '3',
        name: 'Savings (Stable)',
        address: '0xabcd...efgh',
        balance: 22000,
        currency: 'USD',
        lastUpdated: '2024-06-22T11:45:00Z',
      },
    ];

    const filteredWallets = search
      ? mockWallets.filter(w => w.name.toLowerCase().includes(search.toLowerCase()))
      : mockWallets;

    const start = (page - 1) * limit;
    const end = start + limit;
    const paginatedWallets = filteredWallets.slice(start, end);

    return HttpResponse.json({
      wallets: paginatedWallets,
      total: filteredWallets.length,
      page,
      limit,
    });
  }),
  http.get(`${API_URL}/wallets/:id`, ({ params }) => {
    const { id } = params as { id: string };
    const wallet = {
      id,
      name: id === '1' ? 'Main Wallet' : id === '2' ? 'Trading Wallet' : 'Savings Wallet',
      address: id === '1' ? '0x1234...5678' : id === '2' ? '0x8765...4321' : '0xabcd...efgh',
      balance: id === '1' ? 15000 : id === '2' ? 8500 : 22000,
      currency: 'USD',
      lastUpdated: new Date().toISOString(),
      trend: [
        { date: '2024-06-18', balance: 12000 },
        { date: '2024-06-19', balance: 13000 },
        { date: '2024-06-20', balance: 14000 },
        { date: '2024-06-21', balance: 14500 },
        { date: '2024-06-22', balance: id === '1' ? 15000 : id === '2' ? 8500 : 22000 },
      ],
    };
    return HttpResponse.json(wallet);
  }),
  http.get(`${API_URL}/wallets/:id/transactions`, ({ params }) => {
    const { id } = params as { id: string };
    const transactions = [
      {
        id: `${id}-t1`,
        date: '2024-06-21T10:00:00Z',
        type: 'deposit',
        amount: 500,
        currency: 'USD',
        balanceAfter: 15000,
      },
      {
        id: `${id}-t2`,
        date: '2024-06-20T14:30:00Z',
        type: 'trade',
        amount: -200,
        currency: 'USD',
        balanceAfter: 14500,
      },
      {
        id: `${id}-t3`,
        date: '2024-06-19T09:45:00Z',
        type: 'withdraw',
        amount: -300,
        currency: 'USD',
        balanceAfter: 14700,
      },
    ];
    return HttpResponse.json(transactions);
  }),
  http.get('/health', () => {
    return new HttpResponse(null, { status: 200 });
  }),
];

export default handlers;
