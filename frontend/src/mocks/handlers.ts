// @ts-nocheck
import { http, HttpResponse } from 'msw';

const handlers = [
  http.get('/api/v1/timeline', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ data: [] }));
  }),
  http.get('/api/v1/dashboard/overview', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        totalWallets: 12,
        totalBalance: 45230,
        dailyVolume: 3210,
        chart: [
          { date: '2024-06-18', balance: 42000 },
          { date: '2024-06-19', balance: 43000 },
          { date: '2024-06-20', balance: 44000 },
          { date: '2024-06-21', balance: 44500 },
          { date: '2024-06-22', balance: 45230 },
        ],
      })
    );
  }),
  http.get('/api/v1/wallets', (req, res, ctx) => {
    const url = new URL(req.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const search = url.searchParams.get('search') || '';

    const mockWallets = [
      { id: '1', name: 'Main Wallet', address: '0x1234...5678', balance: 15000, currency: 'USD', lastUpdated: '2024-06-22T10:30:00Z' },
      { id: '2', name: 'Trading Wallet', address: '0x8765...4321', balance: 8500, currency: 'USD', lastUpdated: '2024-06-22T09:15:00Z' },
      { id: '3', name: 'Savings Wallet', address: '0xabcd...efgh', balance: 22000, currency: 'USD', lastUpdated: '2024-06-22T11:45:00Z' },
    ];

    const filteredWallets = search 
      ? mockWallets.filter(w => w.name.toLowerCase().includes(search.toLowerCase()))
      : mockWallets;

    const start = (page - 1) * limit;
    const end = start + limit;
    const paginatedWallets = filteredWallets.slice(start, end);

    return res(
      ctx.status(200),
      ctx.json({
        wallets: paginatedWallets,
        total: filteredWallets.length,
        page,
        limit,
      })
    );
  }),
];

export default handlers;
