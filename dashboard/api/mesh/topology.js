// GET /api/mesh/topology - Returns mesh network topology

export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  const now = Date.now();
  
  const topology = {
    nodes: [
      {
        node_id: 'archi-001',
        name: 'ARCHI',
        type: 'expert',
        status: 'online',
        load: Math.floor(30 + Math.random() * 40),
        vram_used: 2.1 + Math.random() * 1.5,
        vram_total: 12,
        last_heartbeat: new Date(now - Math.random() * 5000).toISOString(),
        specialties: ['architecture', 'design']
      },
      {
        node_id: 'devo-001',
        name: 'DEVO',
        type: 'expert',
        status: 'online',
        load: Math.floor(45 + Math.random() * 35),
        vram_used: 3.8 + Math.random() * 2,
        vram_total: 12,
        last_heartbeat: new Date(now - Math.random() * 3000).toISOString(),
        specialties: ['development', 'coding']
      },
      {
        node_id: 'analyst-001',
        name: 'ANALYST',
        type: 'expert',
        status: 'online',
        load: Math.floor(25 + Math.random() * 30),
        vram_used: 1.5 + Math.random() * 1,
        vram_total: 12,
        last_heartbeat: new Date(now - Math.random() * 4000).toISOString(),
        specialties: ['analysis', 'data']
      },
      {
        node_id: 'sentinel-001',
        name: 'SENTINEL',
        type: 'expert',
        status: 'online',
        load: Math.floor(20 + Math.random() * 25),
        vram_used: 1.2 + Math.random() * 0.8,
        vram_total: 12,
        last_heartbeat: new Date(now - Math.random() * 6000).toISOString(),
        specialties: ['security', 'monitoring']
      },
      {
        node_id: 'scribe-001',
        name: 'SCRIBE',
        type: 'expert',
        status: 'online',
        load: Math.floor(35 + Math.random() * 30),
        vram_used: 2.4 + Math.random() * 1.2,
        vram_total: 12,
        last_heartbeat: new Date(now - Math.random() * 2000).toISOString(),
        specialties: ['research', 'documentation']
      },
      {
        node_id: 'nexus-001',
        name: 'NEXUS',
        type: 'coordinator',
        status: 'online',
        load: Math.floor(15 + Math.random() * 20),
        vram_used: 0.5 + Math.random() * 0.3,
        vram_total: 12,
        last_heartbeat: new Date(now - Math.random() * 1000).toISOString(),
        specialties: ['coordination', 'routing']
      }
    ],
    connections: [
      { from: 'nexus-001', to: 'archi-001', weight: 0.9, active: true },
      { from: 'nexus-001', to: 'devo-001', weight: 0.95, active: true },
      { from: 'nexus-001', to: 'analyst-001', weight: 0.85, active: true },
      { from: 'nexus-001', to: 'sentinel-001', weight: 0.88, active: true },
      { from: 'nexus-001', to: 'scribe-001', weight: 0.92, active: true },
      { from: 'archi-001', to: 'devo-001', weight: 0.78, active: Math.random() > 0.3 },
      { from: 'devo-001', to: 'analyst-001', weight: 0.65, active: Math.random() > 0.4 },
      { from: 'sentinel-001', to: 'devo-001', weight: 0.72, active: Math.random() > 0.5 },
      { from: 'scribe-001', to: 'archi-001', weight: 0.68, active: Math.random() > 0.4 }
    ],
    alive: 6,
    total: 6,
    mesh_health: 'optimal',
    last_topology_update: new Date().toISOString()
  };
  
  return res.status(200).json(topology);
}
