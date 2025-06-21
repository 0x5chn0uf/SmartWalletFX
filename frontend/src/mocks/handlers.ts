// @ts-nocheck
import { http, HttpResponse } from 'msw';

const handlers = [
  http.get('/api/v1/timeline', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ data: [] }));
  }),
];

export default handlers;
