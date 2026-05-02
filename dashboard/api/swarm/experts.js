// GET /api/swarm/experts - Returns list of available experts

const EXPERTS = [
  {
    role: 'architect',
    name: 'ARCHI',
    background: 'Senior Systems Architect with expertise in distributed systems and AI infrastructure',
    specialties: ['System Design', 'Architecture Patterns', 'Scalability', 'Technical Strategy'],
    avatar_color: '#ff9900',
    skills: ['FileSkill', 'MCPToolSkill', 'EmbeddingSkill'],
    agent_id: 'archi-001',
    subagent_count: 0,
    memory: { short_term: 12, long_term: 156, total_tokens: 45000 },
    stack: { status: 'active', layers: ['reasoning', 'planning', 'execution'] }
  },
  {
    role: 'developer',
    name: 'DEVO',
    background: 'Lead Developer specializing in code implementation and optimization',
    specialties: ['Code Implementation', 'Debugging', 'Optimization', 'Best Practices'],
    avatar_color: '#33ccff',
    skills: ['FileSkill', 'CodeAnalysisSkill', 'TestingSkill'],
    agent_id: 'devo-001',
    subagent_count: 2,
    memory: { short_term: 18, long_term: 234, total_tokens: 67000 },
    stack: { status: 'active', layers: ['coding', 'testing', 'review'] }
  },
  {
    role: 'analyst',
    name: 'ANALYST',
    background: 'Data Intelligence Officer focused on pattern recognition and insights',
    specialties: ['Data Analysis', 'Pattern Recognition', 'Metrics', 'Insights'],
    avatar_color: '#cc99cc',
    skills: ['EmbeddingSkill', 'DataProcessingSkill', 'VisualizationSkill'],
    agent_id: 'analyst-001',
    subagent_count: 1,
    memory: { short_term: 8, long_term: 189, total_tokens: 52000 },
    stack: { status: 'active', layers: ['analysis', 'synthesis', 'reporting'] }
  },
  {
    role: 'security',
    name: 'SENTINEL',
    background: 'Security Chief responsible for threat detection and system hardening',
    specialties: ['Security Auditing', 'Threat Modeling', 'Access Control', 'Vulnerability Assessment'],
    avatar_color: '#66cc66',
    skills: ['SecurityScanSkill', 'AuditSkill', 'MonitoringSkill'],
    agent_id: 'sentinel-001',
    subagent_count: 0,
    memory: { short_term: 6, long_term: 145, total_tokens: 38000 },
    stack: { status: 'active', layers: ['scanning', 'assessment', 'remediation'] }
  },
  {
    role: 'researcher',
    name: 'SCRIBE',
    background: 'Research Archivist specializing in knowledge synthesis and documentation',
    specialties: ['Documentation', 'Knowledge Synthesis', 'Research', 'Learning'],
    avatar_color: '#ffcc00',
    skills: ['DocIngestionSkill', 'WebSearchSkill', 'SummarizationSkill'],
    agent_id: 'scribe-001',
    subagent_count: 0,
    memory: { short_term: 15, long_term: 312, total_tokens: 89000 },
    stack: { status: 'active', layers: ['research', 'synthesis', 'documentation'] }
  }
];

export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  return res.status(200).json(EXPERTS);
}
