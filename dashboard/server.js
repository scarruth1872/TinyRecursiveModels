// Development API server for local testing
// Run with: node server.js (alongside vite dev server)

import express from 'express';
import cors from 'cors';
import chatHandler from './api/chat.js';

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

// Wrap Vercel serverless function for Express
app.post('/api/chat', async (req, res) => {
  // Create a mock res object that matches Vercel's API
  const mockRes = {
    status: (code) => ({
      json: (data) => res.status(code).json(data),
      end: () => res.status(code).end(),
    }),
    setHeader: (key, value) => res.setHeader(key, value),
    json: (data) => res.json(data),
  };
  
  await chatHandler(req, mockRes);
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`[API Server] Running on http://localhost:${PORT}`);
  console.log(`[API Server] Chat endpoint: http://localhost:${PORT}/api/chat`);
});
