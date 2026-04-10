// GET /api/learning/skills - Returns learned skills status

export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  const skills = [
    {
      name: 'FileSkill',
      description: 'Read and write files in the codebase',
      status: 'active',
      usage_count: 1245,
      last_used: new Date(Date.now() - 60000).toISOString(),
      agents: ['DEVO', 'ARCHI', 'SCRIBE']
    },
    {
      name: 'WebSearchSkill',
      description: 'Search the web for information',
      status: 'active',
      usage_count: 567,
      last_used: new Date(Date.now() - 300000).toISOString(),
      agents: ['SCRIBE', 'ANALYST']
    },
    {
      name: 'EmbeddingSkill',
      description: 'Generate and query vector embeddings',
      status: 'active',
      usage_count: 2340,
      last_used: new Date(Date.now() - 120000).toISOString(),
      agents: ['ANALYST', 'SCRIBE', 'ARCHI']
    },
    {
      name: 'MCPToolSkill',
      description: 'Call MCP microservices and tools',
      status: 'active',
      usage_count: 890,
      last_used: new Date(Date.now() - 180000).toISOString(),
      agents: ['DEVO', 'ARCHI']
    },
    {
      name: 'SecurityScanSkill',
      description: 'Scan code for security vulnerabilities',
      status: 'active',
      usage_count: 234,
      last_used: new Date(Date.now() - 600000).toISOString(),
      agents: ['SENTINEL']
    },
    {
      name: 'DocIngestionSkill',
      description: 'Ingest and process documentation',
      status: 'active',
      usage_count: 456,
      last_used: new Date(Date.now() - 900000).toISOString(),
      agents: ['SCRIBE']
    },
    {
      name: 'TRMInferenceSkill',
      description: 'Run TRM recursive reasoning inference',
      status: 'active',
      usage_count: 123,
      last_used: new Date(Date.now() - 1200000).toISOString(),
      agents: ['ARCHI', 'ANALYST']
    }
  ];
  
  return res.status(200).json({ 
    skills,
    total: skills.length,
    active: skills.filter(s => s.status === 'active').length
  });
}
