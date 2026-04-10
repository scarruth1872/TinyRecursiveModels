// GET /api/system/resources - Returns system resource status

export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  const resources = {
    cpu: {
      percent: 35 + Math.random() * 30,
      cores: 16,
      threads: 24,
      frequency_mhz: 3400
    },
    memory: {
      total_gb: 64,
      used_gb: 28 + Math.random() * 12,
      available_gb: 24 + Math.random() * 8,
      percent: 55 + Math.random() * 20
    },
    gpu: {
      name: 'NVIDIA RTX 4090',
      vram_total_gb: 24,
      vram_used_gb: 12 + Math.random() * 6,
      vram_available_gb: 6 + Math.random() * 4,
      temperature_c: 55 + Math.random() * 15,
      utilization_percent: 40 + Math.random() * 35
    },
    disk: {
      total_gb: 1000,
      used_gb: 450 + Math.random() * 50,
      available_gb: 500 + Math.random() * 50
    },
    network: {
      bytes_sent: Math.floor(Math.random() * 1000000000),
      bytes_recv: Math.floor(Math.random() * 2000000000),
      packets_sent: Math.floor(Math.random() * 1000000),
      packets_recv: Math.floor(Math.random() * 2000000)
    },
    processes: {
      total: 285 + Math.floor(Math.random() * 30),
      running: 12 + Math.floor(Math.random() * 8),
      sleeping: 260 + Math.floor(Math.random() * 20)
    },
    uptime_seconds: Math.floor((Date.now() - 1712700000000) / 1000)
  };
  
  return res.status(200).json(resources);
}
