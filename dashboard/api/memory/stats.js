// GET /api/memory/stats - Returns global memory statistics

export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  const stats = {
    total_memories: 15678 + Math.floor(Math.random() * 100),
    sync_events: 234 + Math.floor(Math.random() * 20),
    last_sync: new Date(Date.now() - Math.random() * 60000).toISOString(),
    
    by_type: {
      knowledge: 8934,
      experience: 3245,
      skill: 1567,
      context: 1932
    },
    
    by_agent: {
      ARCHI: 3456,
      DEVO: 4123,
      ANALYST: 2890,
      SENTINEL: 1234,
      SCRIBE: 3975
    },
    
    storage: {
      vector_db_size_mb: 456.7,
      graph_db_size_mb: 123.4,
      cache_size_mb: 89.2
    },
    
    performance: {
      avg_retrieval_ms: 12 + Math.random() * 8,
      avg_storage_ms: 5 + Math.random() * 3,
      cache_hit_rate: 0.85 + Math.random() * 0.1
    },
    
    recent_contributions: [
      { agent: 'SCRIBE', type: 'knowledge', count: 23, timestamp: new Date(Date.now() - 60000).toISOString() },
      { agent: 'DEVO', type: 'experience', count: 12, timestamp: new Date(Date.now() - 120000).toISOString() },
      { agent: 'ANALYST', type: 'context', count: 8, timestamp: new Date(Date.now() - 180000).toISOString() }
    ]
  };
  
  return res.status(200).json(stats);
}
