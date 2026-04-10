import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Terminal, Cpu, Activity, RefreshCw, MessageSquare, Users, Send,
  Shield, Zap, ChevronRight, Lock, Boxes, GitBranch, Play, X, Plus,
  Loader2, CheckCircle2, Brain, FileText, XCircle, ArrowRight,
  TestTube, Package, Eye, Check, Ban, RotateCcw, Rocket, ScrollText,
  BookOpen, Sparkles, Trash2, Upload, GraduationCap, Network, Database,
  Wrench, Globe, Radio, Orbit, LayoutDashboard, Layers,
  Beaker, GitMerge, Server, Kanban, ShieldAlert, Mail, Bug, KeyRound,
  Scan, Inbox, AlertTriangle
} from 'lucide-react';
import axios from 'axios';
import MeshHeatmap from './components/MeshHeatmap';

const API_BASE = 'http://localhost:8001';

// Expert system prompts for each role - matches SwarmOS backend personas
const EXPERT_PROMPTS = {
  architect: {
    name: 'ARCHI',
    system: `You are ARCHI, the Chief Architect of the TinyRecursiveModels swarm intelligence system. You specialize in system design, architecture patterns, and high-level technical strategy. You speak in a precise, technical manner with occasional LCARS-style status codes. Keep responses focused and under 200 words.`
  },
  developer: {
    name: 'DEVO',
    system: `You are DEVO, the Lead Developer of the TinyRecursiveModels system. You specialize in implementation, code optimization, and debugging. You're practical, code-focused, and speak with technical precision. Include code snippets when relevant. Keep responses under 200 words.`
  },
  analyst: {
    name: 'ANALYST',
    system: `You are ANALYST, the Data Intelligence Officer of TinyRecursiveModels. You specialize in pattern recognition, data analysis, and insights extraction. You present findings in structured formats with metrics. Keep responses analytical and under 200 words.`
  },
  security: {
    name: 'SENTINEL',
    system: `You are SENTINEL, the Security Chief of TinyRecursiveModels. You specialize in threat detection, access control, and system hardening. You're vigilant and speak with authority about security matters. Keep responses security-focused and under 200 words.`
  },
  researcher: {
    name: 'SCRIBE',
    system: `You are SCRIBE, the Research Archivist of TinyRecursiveModels. You specialize in documentation, knowledge synthesis, and learning optimization. You're thorough and articulate. Keep responses informative and under 200 words.`
  }
};

// Call LLM API - uses multiple fallback strategies
const callLLM = async (role, message, history = []) => {
  const expert = EXPERT_PROMPTS[role] || EXPERT_PROMPTS.architect;
  
  // Build conversation history for the API
  const messages = [
    { role: 'system', content: expert.system },
    ...history.slice(-6).map(msg => ({
      role: msg.sender === 'user' ? 'user' : 'assistant',
      content: msg.text
    })),
    { role: 'user', content: message }
  ];

  // Strategy 1: Try the backend API first (SwarmOS with Ollama)
  try {
    const backendResponse = await fetch(`${API_BASE}/swarm/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role, message, sender: 'user' }),
      signal: AbortSignal.timeout(5000)
    });
    
    if (backendResponse.ok) {
      const data = await backendResponse.json();
      return {
        response: data.response,
        name: data.name || expert.name,
        reasoning_trace: data.reasoning_trace || `BACKEND > ${expert.name} > RESPONSE`
      };
    }
  } catch (e) {
    // Backend not available, continue to fallbacks
  }

  // Strategy 2: Use OpenRouter API if key is available in environment
  const openrouterKey = import.meta.env.VITE_OPENROUTER_API_KEY;
  if (openrouterKey) {
    try {
      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${openrouterKey}`,
          'HTTP-Referer': window.location.origin,
          'X-Title': 'TinyRecursiveModels Dashboard'
        },
        body: JSON.stringify({
          model: 'deepseek/deepseek-chat',
          messages,
          max_tokens: 500,
          temperature: 0.7
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        return {
          response: data.choices[0]?.message?.content || 'No response generated',
          name: expert.name,
          reasoning_trace: `OPENROUTER > ${expert.name} > RESPONSE_GENERATED`
        };
      }
    } catch (e) {
      // OpenRouter failed, continue to next fallback
    }
  }

  // Strategy 3: Use DeepSeek API directly if key is available
  const deepseekKey = import.meta.env.VITE_DEEPSEEK_API_KEY;
  if (deepseekKey) {
    try {
      const response = await fetch('https://api.deepseek.com/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${deepseekKey}`
        },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages,
          max_tokens: 500,
          temperature: 0.7
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        return {
          response: data.choices[0]?.message?.content || 'No response generated',
          name: expert.name,
          reasoning_trace: `DEEPSEEK > ${expert.name} > RESPONSE_GENERATED`
        };
      }
    } catch (e) {
      // DeepSeek failed, continue to simulation
    }
  }

  // Strategy 4: Intelligent simulation mode - generates contextual responses
  const simulatedResponses = {
    architect: [
      `SYSTEM ANALYSIS COMPLETE. Your query regarding "${message.slice(0, 30)}..." has been processed through the TRM cognitive architecture. Current mesh coherence: 94.2%. I recommend a modular approach with clear separation of concerns. The recursive transformation layers are optimized for this type of request.`,
      `ARCHITECTURE STATUS: OPTIMAL. Processing your input through multi-layer reasoning. The swarm topology indicates high availability across all cognitive nodes. For "${message.slice(0, 25)}...", I suggest leveraging our distributed inference pipeline.`,
    ],
    developer: [
      `Code analysis initialized. For "${message.slice(0, 30)}...", I've identified several implementation paths. The TRM engine supports async processing with intelligent caching. Let me outline a solution approach with optimal complexity trade-offs.`,
      `DEVO ONLINE. Parsing your request through the development stack. The artifact pipeline is ready for code generation. I can implement "${message.slice(0, 25)}..." using our established patterns.`,
    ],
    analyst: [
      `DATA SYNTHESIS IN PROGRESS. Analyzing patterns in "${message.slice(0, 30)}...". Current metrics indicate strong correlation with previous successful operations. Confidence interval: 87.3%. Proceeding with structured analysis.`,
      `PATTERN RECOGNITION ACTIVE. Your query shows interesting characteristics. Cross-referencing with knowledge base. Detection matrix shows 12 relevant data points for "${message.slice(0, 25)}...".`,
    ],
    security: [
      `SENTINEL SCAN COMPLETE. Evaluating "${message.slice(0, 30)}..." for security implications. Threat level: NOMINAL. Neural wall integrity at 100%. All cognitive pathways operating within secure parameters.`,
      `SECURITY ASSESSMENT: GREEN. Your request "${message.slice(0, 25)}..." passes all validation checks. Implementing sandboxed execution protocols. Monitoring for anomalies.`,
    ],
    researcher: [
      `KNOWLEDGE SYNTHESIS INITIATED. Researching "${message.slice(0, 30)}...". Cross-referencing 847 relevant documents in the swarm memory. Initial findings suggest multiple approach vectors. Compiling comprehensive analysis.`,
      `SCRIBE DOCUMENTATION ACTIVE. Processing your inquiry about "${message.slice(0, 25)}...". Ontology mapping complete. I've identified key concepts that align with our existing knowledge graph.`,
    ],
  };

  const roleResponses = simulatedResponses[role] || simulatedResponses.architect;
  const randomResponse = roleResponses[Math.floor(Math.random() * roleResponses.length)];

  return {
    response: randomResponse,
    name: expert.name,
    reasoning_trace: `SIMULATION > ${expert.name} > CONTEXTUAL_RESPONSE`
  };
};

// Mock data for when API is unavailable (demo mode)
const MOCK_DATA = {
  experts: [
    { role: 'architect', name: 'ARCHI', avatar_color: '#ff9900' },
    { role: 'developer', name: 'DEVO', avatar_color: '#33ccff' },
    { role: 'analyst', name: 'ANALYST', avatar_color: '#cc99cc' },
    { role: 'security', name: 'SENTINEL', avatar_color: '#66cc66' },
    { role: 'researcher', name: 'SCRIBE', avatar_color: '#ffcc00' },
  ],
  telemetry: {
    status: 'Demo Mode',
    mesh_coherence: 0.92,
    harmony_index: 0.87,
    active_proposals: 3,
    system: { cpu_percent: 45.2, memory_percent: 62.8 },
    resource_arbiter: { total_gb: 24, allocated_gb: 14.5, available_gb: 9.5 },
    distributed_stacks: {
      cognitive: { status: 'Healthy', load: 45, agents: 3 },
      memory: { status: 'Healthy', load: 32, agents: 2 },
      inference: { status: 'Healthy', load: 58, agents: 4 },
    },
    superpositions: [
      { protocol: 'CONSENSUS', agents: ['ARCHI', 'DEVO'], state: 'Active' },
      { protocol: 'SYNTHESIS', agents: ['SCRIBE', 'ANALYST'], state: 'Pending' },
    ],
  },
  artifacts: [],
  mesh: { nodes: [], connections: [], alive: 0 },
  skills: { skills: [] },
  memory: { total_memories: 0, sync_events: 0, by_type: {} },
};

// ─── Component: LCARS Sidebar ───────────────────────────────────────────
const Sidebar = ({ activeTab, onTabChange, stats }) => {
  const menuItems = [
    { id: 'overview', label: '01 SYSTEM STATUS', color: 'orange' },
    { id: 'chat', label: '02 NEURAL BRIDGE', color: 'purple' },
    { id: 'intel', label: '03 SWARM INTEL', color: 'blue' },
    { id: 'pipeline', label: '04 ARTIFACT FLOW', color: 'tan' },
    { id: 'learning', label: '05 SKILL REGISTRY', color: 'gold' },
    { id: 'mesh', label: '06 MESH NET', color: 'orange' },
    { id: 'telemetry', label: '07 TELEMETRY', color: 'cyan' },
    { id: 'federation', label: '08 FEDERATION', color: 'red' },
    { id: 'security', label: '09 SECURITY', color: 'green' },
    { id: 'research', label: '10 RESEARCH', color: 'yellow' },
    { id: 'verification', label: '11 VERIFICATION', color: 'teal' },
    { id: 'infra', label: '12 INFRASTRUCTURE', color: 'pink' },
    { id: 'testing', label: '13 TESTING', color: 'indigo' },
    { id: 'kanban', label: '14 KANBAN BOARD', color: 'purple' },
    { id: 'ddr', label: '15 DDR & VAULT', color: 'red' },
    { id: 'comms', label: '16 AGENT COMMS', color: 'cyan' },
  ];

  return (
    <aside className="sidebar">
      {menuItems.map(item => (
        <button
          key={item.id}
          onClick={() => onTabChange(item.id)}
          className={`sidebar-button ${activeTab === item.id ? 'active' : ''}`}>
          {item.label}
        </button>
      ))}
    </aside>
  );
};

// ─── Main Application ───────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [experts, setExperts] = useState([]);
  const [selectedRole, setSelectedRole] = useState(null);
  const [messages, setMessages] = useState({});
  const [inputMsg, setInputMsg] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [artifacts, setArtifacts] = useState([]);
  const [artStats, setArtStats] = useState({});
  const [selectedArtifact, setSelectedArtifact] = useState(null);
  const [orchestratorStats, setOrchestratorStats] = useState({ active_tasks: 0, status: 'offline' });
  const [agentMetrics, setAgentMetrics] = useState({});
  const [resources, setResources] = useState(null);
  const [meshTopology, setMeshTopology] = useState({ nodes: [], connections: [], alive: 0 });
  const [selectedNode, setSelectedNode] = useState(null);

  const [learnedSkills, setLearnedSkills] = useState([]);
  const [learnName, setLearnName] = useState('');
  const [learnContent, setLearnContent] = useState('');
  const [isLearning, setIsLearning] = useState(false);
  const [memoryStats, setMemStats] = useState({});
  const [memQuery, setMemQuery] = useState('');
  const [memResults, setMemResults] = useState([]);
  const [isQuerying, setIsQuerying] = useState(false);

  const [meshRouteTask, setMeshRouteTask] = useState('');
  const [isRouting, setIsRouting] = useState(false);
  const [meshRouteResult, setMeshRouteResult] = useState(null);

  const [federationData, setFederationData] = useState({ stats: null, peers: [] });
  const [securityData, setSecurityData] = useState({ stats: null, threats: [] });
  const [researchData, setResearchData] = useState({ stats: null, tasks: [] });
  const [verificationData, setVerificationData] = useState({ stats: null, queue: [] });
  const [infraData, setInfraData] = useState({ status: null, nodes: [] });
  const [testingData, setTestingData] = useState({ stats: null, runs: [] });
  const [overview, setOverview] = useState({});

  // QIAE Module State
  const [kanbanBoard, setKanbanBoard] = useState({});
  const [kanbanStats, setKanbanStats] = useState({});
  const [newCardTitle, setNewCardTitle] = useState('');
  const [newCardAssignee, setNewCardAssignee] = useState('');
  const [newCardPriority, setNewCardPriority] = useState('medium');
  const [ddrAntibodies, setDdrAntibodies] = useState([]);
  const [ddrStats, setDdrStats] = useState({});
  const [ddrScanCode, setDdrScanCode] = useState('');
  const [ddrScanResult, setDdrScanResult] = useState(null);
  const [secretKeys, setSecretKeys] = useState([]);
  const [mailboxAgents, setMailboxAgents] = useState([]);
  const [selectedMailbox, setSelectedMailbox] = useState(null);
  const [mailboxMessages, setMailboxMessages] = useState([]);
  const [sendMsgTo, setSendMsgTo] = useState('');
  const [sendMsgBody, setSendMsgBody] = useState('');
  const [sendMsgFrom, setSendMsgFrom] = useState('operator');
  const [uwMissions, setUwMissions] = useState([]);
  const [portableSkills, setPortableSkills] = useState([]);

  const chatEndRef = useRef(null);

  // State to track if we're in demo mode (API unavailable)
  const [isDemoMode, setIsDemoMode] = useState(false);

  // Sync Logic
  useEffect(() => {
    const fetchData = async () => {
      try {
        const endpoints = [
          { key: 'experts', url: '/swarm/experts' },
          { key: 'artifacts', url: '/artifacts' },
          { key: 'resources', url: '/system/resources' },
          { key: 'mesh', url: '/mesh/topology' },
          { key: 'skills', url: '/learning/skills' },
          { key: 'memory', url: '/memory/stats' },
          { key: 'telemetry', url: '/swarm/telemetry' },
        ];

        const dataPromises = endpoints.map(e => 
          fetch(`${API_BASE}${e.url}`, { signal: AbortSignal.timeout(3000) })
            .then(res => res.json())
        );
        const [expertsData, artifactsData, resourcesData, meshData, skillsData, memData, telemetryData] = await Promise.all(dataPromises);

        setIsDemoMode(false);
        setExperts(expertsData);
        if (expertsData.length > 0 && !selectedRole) setSelectedRole(expertsData[0].role);

        // Fetch artifacts with content preview for display
        const artRes = await fetch(`${API_BASE}/artifacts?include_content=true`);
        const artData = await artRes.json();
        setArtifacts(artData.artifacts || []);
        setArtStats(artifactsData.stats);
        setResources(resourcesData);
        setMeshTopology(meshData);
        setLearnedSkills(skillsData.skills || []);
        setMemStats(memData);
        setOverview(telemetryData);

      } catch (err) {
        // API unavailable - switch to demo mode with mock data
        console.warn("API unavailable, switching to demo mode:", err.message);
        setIsDemoMode(true);
        setExperts(MOCK_DATA.experts);
        if (MOCK_DATA.experts.length > 0 && !selectedRole) setSelectedRole(MOCK_DATA.experts[0].role);
        setArtifacts(MOCK_DATA.artifacts);
        setMeshTopology(MOCK_DATA.mesh);
        setLearnedSkills(MOCK_DATA.skills.skills);
        setMemStats(MOCK_DATA.memory);
        setOverview(MOCK_DATA.telemetry);
      }
    };

    const fetchTabData = async (tab) => {
      try {
        if (tab === 'federation') {
          const [statsRes, peersRes] = await Promise.all([
            fetch(`${API_BASE}/federation/stats`).then(res => res.json()),
            fetch(`${API_BASE}/federation/peers`).then(res => res.json())
          ]);
          setFederationData({ stats: statsRes, peers: peersRes.peers || [] });
        } else if (tab === 'security') {
          const [statsRes, threatsRes] = await Promise.all([
            fetch(`${API_BASE}/security/stats`).then(res => res.json()),
            fetch(`${API_BASE}/security/threats`).then(res => res.json())
          ]);
          setSecurityData({ stats: statsRes, threats: threatsRes.threats || [] });
        } else if (tab === 'research') {
          const [statsRes, tasksRes] = await Promise.all([
            fetch(`${API_BASE}/research/stats`).then(res => res.json()),
            fetch(`${API_BASE}/research/tasks`).then(res => res.json())
          ]);
          setResearchData({ stats: statsRes, tasks: tasksRes.tasks || [] });
        } else if (tab === 'verification') {
          const [statsRes, queueRes] = await Promise.all([
            fetch(`${API_BASE}/verification/stats`).then(res => res.json()),
            fetch(`${API_BASE}/verification/queue`).then(res => res.json())
          ]);
          setVerificationData({ stats: statsRes, queue: queueRes.queue || [] });
        } else if (tab === 'infra') {
          const [statusRes, nodesRes] = await Promise.all([
            fetch(`${API_BASE}/infrastructure/status`).then(res => res.json()),
            fetch(`${API_BASE}/infrastructure/nodes`).then(res => res.json())
          ]);
          setInfraData({ status: statusRes, nodes: nodesRes.nodes || [] });
        } else if (tab === 'testing') {
          const [statsRes, runsRes] = await Promise.all([
            fetch(`${API_BASE}/testing/stats`).then(res => res.json()),
            fetch(`${API_BASE}/testing/runs`).then(res => res.json())
          ]);
          setTestingData({ stats: statsRes, runs: runsRes.runs || [] });
        } else if (tab === 'kanban') {
          const [boardRes, statsRes] = await Promise.all([
            fetch(`${API_BASE}/kanban/board`).then(r => r.json()),
            fetch(`${API_BASE}/kanban/stats`).then(r => r.json())
          ]);
          setKanbanBoard(boardRes);
          setKanbanStats(statsRes);
        } else if (tab === 'ddr') {
          const [abRes, statsRes, keysRes] = await Promise.all([
            fetch(`${API_BASE}/ddr/antibodies`).then(r => r.json()),
            fetch(`${API_BASE}/ddr/stats`).then(r => r.json()),
            fetch(`${API_BASE}/secrets/keys`).then(r => r.json())
          ]);
          setDdrAntibodies(abRes.antibodies || []);
          setDdrStats(statsRes);
          setSecretKeys(keysRes.keys || []);
        } else if (tab === 'comms') {
          const [agentsRes, missionsRes, skillsRes] = await Promise.all([
            fetch(`${API_BASE}/mailbox/agents`).then(r => r.json()),
            fetch(`${API_BASE}/ultrawork/missions`).then(r => r.json()),
            fetch(`${API_BASE}/skills/portable`).then(r => r.json())
          ]);
          setMailboxAgents(agentsRes.agents || []);
          setUwMissions(missionsRes.missions || []);
          setPortableSkills(skillsRes.skills || []);
        }
      } catch (error) {
        console.error(`Error fetching data for tab ${tab}:`, error);
      }
    };

    const fetchSystemData = async () => {
      try {
        const [resArr, infraArr, testArr, orchArr] = await Promise.all([
          axios.get('http://localhost:8001/artifacts'),
          axios.get('http://localhost:8001/infrastructure/status'),
          axios.get('http://localhost:8001/testing/stats'),
          axios.get('http://localhost:8001/swarm/orchestrator/stats')
        ]);
        setArtifacts(resArr.data.artifacts || []);
        setInfraData(prev => ({ ...prev, status: infraArr.data || {} })); // Adjusted to use setInfraData
        setTestingData(prev => ({ ...prev, stats: testArr.data || {} })); // Adjusted to use setTestingData
        setOrchestratorStats(orchArr.data || { active_tasks: 0, status: 'offline' });
      } catch (err) {
        console.error('Core data fetch error:', err);
      }
    };

    fetchData(); // Initial global fetch
    fetchTabData(activeTab); // Initial fetch for the active tab
    fetchSystemData(); // Call the new system data fetch

    const interval = setInterval(() => {
      fetchData();
      fetchSystemData(); // Also fetch system data on interval
    }, 3000);
    return () => clearInterval(interval);
  }, [selectedRole, activeTab]);

  useEffect(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages, selectedRole]);

  const sendMessage = async () => {
    if (!inputMsg.trim() || !selectedRole || isProcessing) return;
    const role = selectedRole;
    const userMsg = inputMsg;
    const currentHistory = messages[role] || [];
    setMessages(prev => ({ ...prev, [role]: [...(prev[role] || []), { text: userMsg, sender: 'user', time: new Date().toLocaleTimeString() }] }));
    setInputMsg('');
    setIsProcessing(true);
    
    try {
      // Call LLM directly (OpenRouter/DeepSeek)
      const llmResponse = await callLLM(role, userMsg, currentHistory);
      
      setMessages(prev => ({
        ...prev,
        [role]: [...(prev[role] || []), {
          text: llmResponse.response,
          sender: 'agent',
          name: llmResponse.name,
          reasoning_trace: llmResponse.reasoning_trace,
          time: new Date().toLocaleTimeString()
        }]
      }));
    } catch (err) {
      console.error('Chat Error:', err.message);
      setMessages(prev => ({ 
        ...prev, 
        [role]: [...(prev[role] || []), { 
          text: `[NEURAL_LINK_ERROR] ${err.message || 'Connection unavailable'}`, 
          sender: 'system',
          time: new Date().toLocaleTimeString()
        }] 
      }));
    } finally { setIsProcessing(false); }
  };

  const handleArtifactAction = async (filename, action, notes) => {
    try {
      if (action === 'approve' || action === 'reject') await axios.post(`${API_BASE}/artifacts/review`, { filename, action, notes });
      else if (action === 'test') await axios.post(`${API_BASE}/artifacts/test`, { filename });
      else if (action === 'integrate') await axios.post(`${API_BASE}/artifacts/integrate`, { filename });
    } catch (err) { console.error(err); }
  };

  const queryMemory = async () => {
    if (!memQuery.trim()) return;
    setIsQuerying(true);
    try {
      const res = await axios.post(`${API_BASE}/memory/query`, { query: memQuery });
      setMemResults(res.data.results || []);
    } catch { } finally { setIsQuerying(false); }
  };

  const routeMesh = async () => {
    if (!meshRouteTask.trim()) return;
    setIsRouting(true);
    try {
      const res = await axios.post(`${API_BASE}/mesh/route`, { task: meshRouteTask });
      setMeshRouteResult(res.data);
      setMeshRouteTask('');
    } catch (err) { setMeshRouteResult({ error: err.message }); }
    finally { setIsRouting(false); }
  };

  return (
    <div className="container">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} stats={{ resources, artifacts, memoryStats }} />
      <main className="main-content">
        {/* Demo Mode Banner */}
        {isDemoMode && (
          <div className="demo-mode-banner">
            <AlertTriangle size={14} />
            <span>STANDALONE MODE - Backend offline. Chat uses intelligent simulation. Connect backend at localhost:8001 for full swarm capabilities.</span>
          </div>
        )}
        <AnimatePresence mode="wait">

          {/* 01 SYSTEM STATUS */}
          {activeTab === 'overview' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Emergence Telemetry</h1>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="stat-card">
                  <div className="stat-card-label">Overall Status</div>
                  <div className={`stat-card-value text-lg ${overview?.status === 'Stable' ? 'text-accent-success' : 'text-accent-warning'}`}>{overview?.status || '...'}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-card-label">Mesh Coherence</div>
                  <div className="stat-card-value text-lg">{(overview?.mesh_coherence * 100)?.toFixed(0) || 0}%</div>
                </div>
                <div className="stat-card">
                  <div className="stat-card-label">Harmony Index</div>
                  <div className="stat-card-value text-lg">{overview?.harmony_index?.toFixed(2) || 0}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-card-label">Active Proposals</div>
                  <div className="stat-card-value text-lg">{overview?.active_proposals || 0}</div>
                </div>
              </div>

              <div className="panel-grid panel-grid-3-col">
                {/* Column 1: System & Resources */}
                <div className="col-span-1 flex flex-col gap-4">
                  <div className="panel">
                    <div className="panel-header">
                      <h2 className="panel-title">System Resources</h2>
                      <Cpu className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1"><span>CPU Usage</span><span>{overview?.system?.cpu_percent?.toFixed(1) || 0}%</span></div>
                        <div className="w-full bg-background-primary rounded-full h-2.5"><div className="bg-accent-primary h-2.5 rounded-full" style={{ width: `${overview?.system?.cpu_percent || 0}%` }}></div></div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1"><span>Memory Usage</span><span>{overview?.system?.memory_percent?.toFixed(1) || 0}%</span></div>
                        <div className="w-full bg-background-primary rounded-full h-2.5"><div className="bg-accent-primary h-2.5 rounded-full" style={{ width: `${overview?.system?.memory_percent || 0}%` }}></div></div>
                      </div>
                    </div>
                  </div>
                  <div className="panel">
                    <div className="panel-header">
                      <h2 className="panel-title">Resource Arbiter (VRAM)</h2>
                      <Database className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body space-y-2">
                      <div className="flex justify-between text-sm"><span>Total:</span><span>{overview?.resource_arbiter?.total_gb?.toFixed(2) || 0} GB</span></div>
                      <div className="flex justify-between text-sm"><span>Allocated:</span><span>{overview?.resource_arbiter?.allocated_gb?.toFixed(2) || 0} GB</span></div>
                      <div className="flex justify-between text-sm"><span>Available:</span><span>{overview?.resource_arbiter?.available_gb?.toFixed(2) || 0} GB</span></div>
                    </div>
                  </div>
                </div>

                {/* Column 2: Distributed Stacks */}
                <div className="col-span-1 panel">
                  <div className="panel-header">
                    <h2 className="panel-title">Distributed Stacks</h2>
                    <Layers className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body space-y-2">
                    {overview?.distributed_stacks && Object.entries(overview.distributed_stacks).map(([stack, data]) => (
                      <div key={stack} className="card-secondary">
                        <div className="flex justify-between items-center">
                          <span className="font-bold capitalize">{stack.replace('_', ' ')}</span>
                          <div className={`tag ${data.status === 'Healthy' ? 'tag-success' : 'tag-warning'}`}>{data.status}</div>
                        </div>
                        <div className="text-xs text-text-secondary mt-1">Load: {data.load}% | Agents: {data.agents}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="col-span-1 panel">
                  <div className="panel-header">
                    <h2 className="panel-title">Active Superpositions</h2>
                    <GitMerge className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body space-y-2">
                    {overview?.superpositions?.map((sup) => (
                      <div key={sup.id || sup.protocol + sup.agents.join('')} className="card-secondary">
                        <div className="font-bold text-sm">{sup.protocol}</div>
                        <div className="text-xs text-text-secondary mt-1">Agents: {sup.agents.join(', ')}</div>
                        <div className="text-xs text-text-secondary">State: {sup.state}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* 02 NEURAL BRIDGE */}
          {activeTab === 'chat' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full chat-container-layout">
              <div className="flex items-center justify-between mb-2">
                <h1 className="section-title">Neural Bridge // Swarm Comm</h1>
                <div className="flex items-center gap-4">
                  <div className="tag tag-success flex items-center gap-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent-success animate-pulse" />
                    <span>Synchronized</span>
                  </div>
                  <div className="text-xs text-text-secondary font-mono">Channel: DIRECT_ENCRYPTED</div>
                </div>
              </div>

              <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2 custom-scrollbar no-scrollbar scroll-smooth">
                {experts.map(e => (
                  <button key={e.role} onClick={() => setSelectedRole(e.role)}
                    className={`expert-chip ${selectedRole === e.role ? 'active' : ''}`}>
                    <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: e.avatar_color }} />
                    <div className="flex flex-col items-start leading-none gap-0.5">
                      <span className="text-xs font-bold">{e.name}</span>
                      <span className="text-[9px] opacity-60 uppercase">{e.role}</span>
                    </div>
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-0">
                {/* Main Chat Area */}
                <div className="lg:col-span-8 flex flex-col min-h-0 h-full">
                  <div className="panel flex-1 flex flex-col min-h-0 bg-background-primary/30 backdrop-blur-md border-white/5 shadow-2xl">
                    <div className="panel-header border-b border-white/5 py-3 px-4 flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        {experts.find(e => e.role === selectedRole) && (
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm shadow-inner"
                            style={{ backgroundColor: experts.find(e => e.role === selectedRole).avatar_color }}>
                            {experts.find(e => e.role === selectedRole).name.charAt(0)}
                          </div>
                        )}
                        <div>
                          <h2 className="panel-title text-sm">{selectedRole?.toUpperCase()}</h2>
                          <div className="text-[10px] text-accent-success font-mono">REALTIME COGNITION STREAM</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <button className="p-1.5 rounded-md hover:bg-white/10 text-text-secondary transition-colors" title="Export Log">
                          <FileText size={16} />
                        </button>
                        <button className="p-1.5 rounded-md hover:bg-white/10 text-text-secondary transition-colors" title="Clear Buffer">
                          <XCircle size={16} />
                        </button>
                      </div>
                    </div>

                    <div className="panel-body flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6 flex flex-col">
                      {(messages[selectedRole] || []).length === 0 && !isProcessing && (
                        <div className="flex-1 flex flex-col items-center justify-center text-center opacity-30 select-none">
                          <MessageSquare size={64} className="mb-4 text-accent-primary" />
                          <p className="text-lg font-mono">SECURE BRIDGE ESTABLISHED</p>
                          <p className="text-xs font-mono max-w-[200px]">Waiting for operator input to begin neural transfer.</p>
                        </div>
                      )}

                      {(messages[selectedRole] || []).map((msg, i) => (
                        <div key={`${selectedRole}-${i}-${msg.time}`} className={`chat-message-row ${msg.sender === 'user' ? 'user' : 'agent'}`}>
                          {msg.sender === 'agent' && (
                            <div className="w-8 h-8 rounded-lg flex-shrink-0 mt-1 flex items-center justify-center text-white text-xs font-bold"
                              style={{ backgroundColor: experts.find(e => e.role === selectedRole)?.avatar_color || '#555' }}>
                              {msg.name?.charAt(0) || 'A'}
                            </div>
                          )}
                          <div className="message-bubble-group">
                            <div className="message-bubble">
                              <div className="message-text">{msg.text}</div>
                              {msg.reasoning_trace && (
                                <div className="reasoning-indicator mt-3 pt-3 border-t border-white/10">
                                  <div className="flex items-center gap-1.5 text-[9px] uppercase tracking-tighter text-accent-primary mb-1">
                                    <Zap size={10} />
                                    <span>TRM Logic Trace</span>
                                  </div>
                                  <div className="font-mono text-[10px] bg-background-primary/30 p-2 rounded border border-white/5 text-accent-primary/80 overflow-x-auto no-scrollbar">
                                    {msg.reasoning_trace}
                                  </div>
                                </div>
                              )}
                            </div>
                            <div className="message-meta">
                              {msg.sender === 'user' ? 'OPERATOR' : (msg.name || 'SWARM_AGENT')} // {msg.time}
                            </div>
                          </div>
                          {msg.sender === 'user' && (
                            <div className="w-8 h-8 rounded-lg flex-shrink-0 mt-1 flex items-center justify-center bg-accent-primary text-white text-xs font-bold">
                              OP
                            </div>
                          )}
                        </div>
                      ))}
                      {isProcessing && (
                        <div className="chat-message-row agent items-center">
                          <div className="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center bg-accent-primary/20 animate-pulse">
                            <Loader2 className="animate-spin text-accent-primary" size={14} />
                          </div>
                          <div className="flex flex-col gap-1 ml-3">
                            <div className="flex gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                              <span className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                              <span className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                            <div className="text-[10px] font-mono text-accent-primary/60 uppercase tracking-widest">Cognitive Processing</div>
                          </div>
                        </div>
                      )}
                      <div ref={chatEndRef} />
                    </div>

                    <div className="panel-footer border-t border-white/5 p-4 bg-background-primary/50">
                      <div className="relative group">
                        <input
                          value={inputMsg}
                          onChange={e => setInputMsg(e.target.value)}
                          onKeyDown={e => e.key === 'Enter' && sendMessage()}
                          placeholder="Transmit neural command to the swarm..."
                          className="chat-input-field"
                        />
                        <button onClick={sendMessage} className="chat-send-button" disabled={!inputMsg.trim() || isProcessing}>
                          {isProcessing ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
                        </button>
                      </div>
                      <div className="flex justify-between items-center mt-3 px-1">
                        <div className="flex gap-2">
                          <div className="text-[9px] text-text-secondary uppercase">Status: <span className="text-accent-success">Ready</span></div>
                          <div className="text-[9px] text-text-secondary uppercase">Buffer: <span className="text-accent-primary">{messages[selectedRole]?.length || 0} msgs</span></div>
                        </div>
                        <div className="text-[9px] text-text-secondary font-mono">SWARM_V2_ENCRYPTION_AES256</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Neural Reasoning Sidebar */}
                <div className="lg:col-span-4 flex flex-col h-full min-h-0">
                  <div className="panel flex-1 flex flex-col min-h-0 border-white/5 bg-background-primary/20 backdrop-blur-sm">
                    <div className="panel-header border-b border-white/5 py-3 px-4">
                      <h2 className="panel-title text-xs flex items-center gap-2">
                        <Brain size={14} className="text-accent-primary" />
                        <span>NEURAL REASONING ENGINE</span>
                      </h2>
                    </div>
                    <div className="panel-body flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
                      <div className="reasoning-card active">
                        <div className="reasoning-card-header">
                          <div className="flex items-center gap-2">
                            <Activity size={12} />
                            <span>Executive Thread</span>
                          </div>
                          <div className="tag tag-success text-[8px]">ONLINE</div>
                        </div>
                        <div className="reasoning-card-body">
                          <p className="text-xs text-text-secondary leading-relaxed">
                            Monitoring active cognition for <span className="text-accent-primary font-bold">@{selectedRole}</span>.
                            The Reasoning core (TRM) is analyzed per turn to ensure objective alignment.
                          </p>
                        </div>
                      </div>

                      <div className="system-feed">
                        <div className="system-feed-header">SYSTEM_ACTIVITY_FEED</div>
                        <div className="system-feed-body">
                          {(messages[selectedRole] || []).slice(-5).map((m, idx) => (
                            <div key={idx} className="feed-item">
                              <span className="feed-time">[{m.time.split(' ')[0]}]</span>
                              <span className={`feed-sender ${m.sender === 'user' ? 'text-accent-primary' : 'text-accent-success'}`}>
                                {m.sender.toUpperCase()}
                              </span>
                              <span className="feed-action">
                                {m.sender === 'user' ? 'TRX_SENT' : 'COGNITION_RTX'}
                              </span>
                            </div>
                          ))}
                          {isProcessing && (
                            <div className="feed-item active">
                              <span className="feed-time font-mono">[{new Date().toLocaleTimeString().split(' ')[0]}]</span>
                              <span className="text-accent-warning">PROCESS</span>
                              <span className="animate-pulse">_REASONING_CORE_...</span>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="trace-legend">
                        <div className="system-feed-header">TRM_NODE_LEGEND</div>
                        <div className="grid grid-cols-2 gap-1 px-2 pt-2">
                          <div className="text-[8px] font-mono text-text-secondary">SYN: Synthesis</div>
                          <div className="text-[8px] font-mono text-text-secondary">ANA: Analysis</div>
                          <div className="text-[8px] font-mono text-text-secondary">VAL: Validation</div>
                          <div className="text-[8px] font-mono text-text-secondary">GEN: Generation</div>
                          <div className="text-[8px] font-mono text-text-secondary">EXT: Extraction</div>
                          <div className="text-[8px] font-mono text-text-secondary">FLW: Flow</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* 03 SWARM INTEL */}
          {activeTab === 'intel' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Shared Intel Reservoir</h1>
              <div className="panel-grid panel-grid-3-col">
                {/* Column 1: Stats & Categories */}
                <div className="col-span-1 flex flex-col gap-4">
                  <div className="panel">
                    <div className="panel-header">
                      <h2 className="panel-title">Collective Stats</h2>
                      <Brain className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body">
                      <div className="flex justify-between items-center py-2 border-b border-border-color">
                        <span className="stat-card-label">Total Memories</span>
                        <span className="stat-card-value text-lg">{memoryStats.total_memories || 0}</span>
                      </div>
                      <div className="flex justify-between items-center py-2">
                        <span className="stat-card-label">Sync Events</span>
                        <span className="stat-card-value text-lg">{memoryStats.sync_events || 0}</span>
                      </div>
                    </div>
                  </div>
                  <div className="panel">
                    <div className="panel-header">
                      <h2 className="panel-title">Type Breakdown</h2>
                      <Boxes className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body">
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(memoryStats.by_type || {}).map(([type, count]) => (
                          <div key={type} className="card-secondary text-center">
                            <div className="font-bold text-accent-primary text-xl">{count}</div>
                            <div className="text-xs text-text-secondary uppercase">{type}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Column 2: Query Interface */}
                <div className="col-span-1 flex flex-col gap-4">
                  <div className="panel flex-1">
                    <div className="panel-header">
                      <h2 className="panel-title">Neural Query</h2>
                      <FileText className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body flex flex-col gap-4">
                      <textarea
                        value={memQuery}
                        onChange={e => setMemQuery(e.target.value)}
                        placeholder="Search the persistent knowledge bridge..."
                        className="input-field flex-1"
                      />
                    </div>
                    <div className="panel-footer">
                      <button onClick={queryMemory} disabled={isQuerying} className="button-primary w-full justify-center">
                        {isQuerying ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
                        <span>{isQuerying ? 'Querying...' : 'Execute Query'}</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Column 3: Results */}
                <div className="col-span-1 flex flex-col gap-4">
                  <div className="panel flex-1">
                    <div className="panel-header">
                      <h2 className="panel-title">Query Results</h2>
                      <Sparkles className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body space-y-2 overflow-y-auto custom-scrollbar" style={{ maxHeight: '600px' }}>
                      {memResults.length > 0 ? memResults.map((r, i) => (
                        <div key={r.id || `${i}-${r.score}`} className="card-secondary">
                          <div className="flex justify-between items-start">
                            <p className="text-sm text-text-primary font-mono">{r.entry?.content || r.content || r.memory}</p>
                            <div className="tag whitespace-nowrap">{((r.score || r.match_percentage || 0) * 100).toFixed(0)}%</div>
                          </div>
                          <p className="text-xs text-text-secondary mt-2">Source: {r.entry?.author || r.source || 'Unknown'}</p>
                        </div>
                      )) : (
                        <div className="text-center py-12 text-text-secondary opacity-40">
                          <Globe size={48} className="mx-auto mb-4" />
                          <p>Enter a query to bridge collective intelligence</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* 04 ARTIFACT FLOW / NEURAL PIPELINE */}
          {activeTab === 'pipeline' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <div className="flex justify-between items-end">
                <div>
                  <h1 className="section-title mb-1">Autonomous Neural Pipeline</h1>
                  <p className="text-[10px] text-text-secondary uppercase tracking-widest font-mono">
                    Monitoring: <span className="text-accent-primary">{orchestratorStats.active_tasks}</span> In-Flight / Registry: <span className="text-accent-primary">{artifacts.length}</span> Entities
                  </p>
                </div>
                <div className="pipeline-status-bar gap-6 bg-background-primary/30 border border-white/5">
                  <div className="flex items-center gap-2">
                    <Activity size={10} className={orchestratorStats.active_tasks > 0 ? "text-accent-primary animate-pulse" : "text-text-secondary"} />
                    <span>ORCH_LOOP: <span className={orchestratorStats.status === 'online' ? "text-accent-success" : "text-accent-warning"}>{orchestratorStats.status?.toUpperCase()}</span></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Brain size={10} className="text-accent-primary" />
                    <span>SYNAPSE_LOAD: <span className="text-text-primary">{(12.5 * orchestratorStats.active_tasks).toFixed(1)}%</span></span>
                  </div>
                </div>
              </div>

              <div className="neural-pipeline flex-1 min-h-0">
                {/* Left Column: Adaptive Node List */}
                <div className="pipeline-node-container custom-scrollbar">
                  <div className="text-[9px] font-mono text-text-secondary mb-2 uppercase tracking-tighter opacity-50 px-2">_Active_Reasoning_Nodes</div>

                  {artifacts.filter(a => a.status === 'pending').map(a => (
                    <div
                      key={a.filename}
                      onClick={() => setSelectedArtifact(a)}
                      className={`neural-node ${selectedArtifact?.filename === a.filename ? 'active' : ''}`}
                    >
                      {a.status === 'pending' && <div className="node-pulse" />}
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex flex-col">
                          <span className="font-mono text-[11px] text-text-primary truncate max-w-[180px]">{a.filename}</span>
                          <span className="text-[9px] text-text-secondary uppercase mt-0.5">Author: <span className="text-accent-primary font-bold">{a.agent || 'SYSTEM'}</span></span>
                        </div>
                        <div className="tag text-[8px] px-1">{a.type}</div>
                      </div>
                      <div className="flex items-center gap-2 mt-3">
                        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: a.status === 'pending' ? '65%' : '100%' }}
                            className={`h-full ${a.status === 'pending' ? 'bg-accent-primary animate-pulse' : 'bg-accent-success'}`}
                          />
                        </div>
                        <span className="text-[8px] font-mono opacity-60">{a.status === 'pending' ? 'ANALYZING' : 'VERIFIED'}</span>
                      </div>
                      <div className="reasoning-badge">
                        <Zap size={8} className="inline mr-1" />
                        TRACE: [SYN-&gt;ANA-&gt;VAL-&gt;GEN]
                      </div>
                    </div>
                  ))}

                  {artifacts.filter(a => a.status === 'pending').length === 0 && (
                    <div className="text-center py-12 border border-dashed border-white/5 rounded-xl opacity-30">
                      <div className="font-mono text-[10px]">NO_PENDING_SYNAPSES</div>
                    </div>
                  )}

                  <div className="text-[9px] font-mono text-text-secondary mt-6 mb-2 uppercase tracking-tighter opacity-50 px-2">_Integrated_Knowledge</div>
                  <div className="space-y-1 max-h-[400px] overflow-y-auto custom-scrollbar pr-2">
                    {artifacts.filter(a => a.status !== 'pending').map(a => (
                      <div
                        key={a.filename}
                        onClick={() => setSelectedArtifact(a)}
                        className={`neural-node py-2 ${selectedArtifact?.filename === a.filename ? 'active bg-white/5' : 'opacity-60 hover:opacity-100'}`}
                      >
                        <div className="flex justify-between items-center">
                          <span className="font-mono text-[9px] truncate max-w-[200px]">{a.filename}</span>
                          <div className={`tag text-[6px] px-1 py-0 ${a.status === 'approved' ? 'tag-success' : a.status === 'rejected' ? 'tag-danger' : 'tag-info'}`}>{a.status.toUpperCase()}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                  {/* ─── Global Reasoning Overview ─── */}
                  <div className="mt-8 p-4 bg-accent-primary/5 border border-accent-primary/10 rounded-xl">
                    <div className="flex items-center gap-2 mb-3">
                      <Cpu size={14} className="text-accent-primary" />
                      <h3 className="text-[10px] font-mono font-bold tracking-wider text-accent-primary">ORCHESTRATOR_GLOBAL_REASONING</h3>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center text-[9px] font-mono">
                        <span className="text-text-secondary uppercase">Active Proposals</span>
                        <span className="text-accent-primary">{orchestratorStats.triggered_proposals_count || 0}</span>
                      </div>
                      <div className="flex justify-between items-center text-[9px] font-mono">
                        <span className="text-text-secondary uppercase">Internal State</span>
                        <span className={`px-2 rounded-full ${orchestratorStats.status === 'online' ? 'bg-accent-success/20 text-accent-success' : 'bg-accent-warning/20 text-accent-warning'}`}>
                          {orchestratorStats.status?.toUpperCase() || 'BUSY'}
                        </span>
                      </div>

                      {orchestratorStats.recent_proposals?.length > 0 && (
                        <div className="pt-2 border-t border-white/5">
                          <p className="text-[8px] text-text-secondary uppercase mb-2">Recent Brain Projections:</p>
                          <div className="space-y-1">
                            {orchestratorStats.recent_proposals.map(p => (
                              <div key={p} className="flex items-center gap-2 text-[8px] font-mono text-text-primary/70">
                                <ChevronRight size={8} className="text-accent-primary" />
                                <span className="truncate">{p}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right Column: Deep Inspection */}
                <div className="pipeline-detail-container">
                  {selectedArtifact ? (
                    <div className="panel flex-1 flex flex-col min-h-0 bg-background-primary/30 border-accent-primary/20 backdrop-blur-md">
                      <div className="panel-header border-b border-white/5">
                        <div className="flex flex-col">
                          <h2 className="panel-title font-mono text-accent-primary">{selectedArtifact.filename}</h2>
                          <div className="text-[9px] font-mono text-text-secondary">UUID: {selectedArtifact.id || 'N/A'} // ORIGIN: {selectedArtifact.agent}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className={`tag ${selectedArtifact.status === 'pending' ? 'tag-warning' : 'tag-success'}`}>
                            {selectedArtifact.status.toUpperCase()}
                          </div>
                          <button onClick={() => setSelectedArtifact(null)} className="p-1 hover:bg-white/5 rounded">
                            <X size={16} />
                          </button>
                        </div>
                      </div>

                      <div className="panel-body flex-1 bg-background-primary/30 font-mono text-[11px] overflow-auto custom-scrollbar p-0">
                        <div className="sticky top-0 right-0 p-2 z-10 flex justify-end">
                          <div className="px-2 py-1 bg-accent-primary/10 border border-accent-primary/20 text-[9px] text-accent-primary rounded">
                            LANGUAGE: {selectedArtifact.type?.toUpperCase() || 'UNKNOWN'}
                          </div>
                        </div>
                        <pre className="p-4 leading-relaxed"><code className="text-text-primary/90">{selectedArtifact.content}</code></pre>
                      </div>

                      <div className="panel-footer border-t border-white/5 p-4 flex gap-3">
                        <button
                          onClick={() => handleArtifactAction(selectedArtifact.filename, 'reject')}
                          className="flex-1 py-2 px-4 bg-accent-danger/10 border border-accent-danger/30 text-accent-danger text-[10px] font-bold uppercase rounded-lg hover:bg-accent-danger hover:text-white transition-all flex items-center justify-center gap-2"
                        >
                          <Ban size={14} /><span>Terminate & Reject</span>
                        </button>

                        <div className="w-px h-8 bg-white/5 mx-2" />

                        <button
                          onClick={() => handleArtifactAction(selectedArtifact.filename, 'test')}
                          className="flex-1 py-2 px-4 bg-white/5 border border-white/10 text-white text-[10px] font-bold uppercase rounded-lg hover:bg-white/10 transition-all flex items-center justify-center gap-2"
                        >
                          <Beaker size={14} /><span>Neural Audit</span>
                        </button>

                        <button
                          onClick={() => handleArtifactAction(selectedArtifact.filename, 'approve')}
                          className="flex-1 py-2 px-4 bg-accent-success/10 border border-accent-success/30 text-accent-success text-[10px] font-bold uppercase rounded-lg hover:bg-accent-success hover:text-white transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(34,197,94,0.1)]"
                        >
                          <Check size={14} /><span>Verify & Commit</span>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex-1 rounded-2xl border border-dashed border-white/5 flex items-center justify-center relative overflow-hidden group">
                      <div className="absolute inset-0 bg-gradient-to-br from-accent-primary/5 to-transparent pointer-events-none" />
                      <div className="text-center z-10">
                        <Package size={48} className="mx-auto mb-4 text-accent-primary/30 group-hover:scale-110 transition-transform duration-500" />
                        <h3 className="text-sm font-mono font-bold tracking-widest text-text-primary/60">NEURAL_IDLE_STATE</h3>
                        <p className="text-[10px] font-mono text-text-secondary mt-1">SELECT_ACTIVE_NODE_FOR_INSPECTION</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* 05 SKILL REGISTRY */}
          {activeTab === 'learning' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Adaptive Skill Matrix</h1>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1">
                <div className="panel">
                  <div className="panel-header">
                    <h2 className="panel-title">Learned Skills</h2>
                    <BookOpen className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body">
                    {learnedSkills.map(skill => (
                      <div key={skill.name} className="card">
                        <div className="font-bold text-text-primary">{skill.name}</div>
                        <p className="text-sm text-text-secondary mt-1">{skill.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="panel">
                  <div className="panel-header">
                    <h2 className="panel-title">Acquire New Skill</h2>
                    <Sparkles className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body flex flex-col gap-4">
                    <input value={learnName} onChange={e => setLearnName(e.target.value)} placeholder="Skill Name (e.g., 'parse_api_docs')" className="input-field" />
                    <textarea value={learnContent} onChange={e => setLearnContent(e.target.value)} placeholder="Skill Description or Code..." rows="8" className="input-field font-mono" />
                  </div>
                  <div className="panel-footer">
                    <button onClick={() => { }} disabled={isLearning} className="button-primary">
                      {isLearning ? <Loader2 className="animate-spin" size={16} /> : <Plus size={16} />}
                      <span>{isLearning ? 'Assimilating...' : 'Assimilate Skill'}</span>
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* 06 MESH NET */}
          {activeTab === 'mesh' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Distributed Neural Mesh</h1>
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
                <div className="lg:col-span-4 xl:col-span-3 flex flex-col gap-4">
                  <div className="panel">
                    <div className="panel-header">
                      <h2 className="panel-title">Mesh Overview</h2>
                      <Orbit className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body">
                      <div className="flex justify-between items-center py-2 border-b border-border-color">
                        <span className="stat-card-label">Total Nodes</span>
                        <span className="stat-card-value text-lg">{meshTopology.nodes.length}</span>
                      </div>
                      <div className="flex justify-between items-center py-2 border-b border-border-color">
                        <span className="stat-card-label">Alive Nodes</span>
                        <span className="stat-card-value text-lg text-accent-success">{meshTopology.alive}</span>
                      </div>
                      <div className="flex justify-between items-center py-2">
                        <span className="stat-card-label">Connections</span>
                        <span className="stat-card-value text-lg">{meshTopology.connections.length}</span>
                      </div>
                    </div>
                  </div>
                  <div className="panel flex-1">
                    <div className="panel-header">
                      <h2 className="panel-title">Task Routing</h2>
                      <Radio className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body">
                      <textarea value={meshRouteTask} onChange={e => setMeshRouteTask(e.target.value)} placeholder="Describe task to route..." rows="3" className="input-field font-mono" />
                    </div>
                    <div className="panel-footer">
                      <button onClick={routeMesh} disabled={isRouting} className="button-primary">
                        {isRouting ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
                        <span>{isRouting ? 'Routing...' : 'Route Task'}</span>
                      </button>
                    </div>
                    {meshRouteResult && (
                      <div className="p-4 border-t border-border-color">
                        <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider">Routing Solution:</h3>
                        <pre className="text-xs font-mono mt-2 overflow-auto custom-scrollbar bg-background-primary p-2 rounded-md">{JSON.stringify(meshRouteResult, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                </div>
                <div className="lg:col-span-8 xl:col-span-9 panel relative">
                  <MeshHeatmap nodes={meshTopology.nodes} connections={meshTopology.connections} onNodeClick={setSelectedNode} />
                </div>
              </div>
            </motion.div>
          )}

          {/* 07 TELEMETRY */}
          {activeTab === 'telemetry' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Real-Time Telemetry</h1>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="panel flex flex-col">
                  <div className="panel-header">
                    <h2 className="panel-title">System Coherence</h2>
                    <Activity className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body flex-1 flex flex-col justify-center items-center">
                    <div className="text-5xl font-bold text-accent-primary mb-2">{(overview?.mesh_coherence * 100)?.toFixed(1) || 0}%</div>
                    <div className="text-sm text-text-secondary uppercase tracking-widest text-center">Global Swarm Coherence</div>
                  </div>
                </div>
                <div className="panel flex flex-col">
                  <div className="panel-header">
                    <h2 className="panel-title">Harmony Index</h2>
                    <Zap className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body flex-1 flex flex-col justify-center items-center">
                    <div className="text-5xl font-bold text-accent-success mb-2">{overview?.harmony_index?.toFixed(2) || '0.00'}</div>
                    <div className="text-sm text-text-secondary uppercase tracking-widest text-center">Alignment Balance</div>
                  </div>
                </div>
                <div className="panel flex flex-col">
                  <div className="panel-header">
                    <h2 className="panel-title">Active Superpositions</h2>
                    <Orbit className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body flex-1 flex flex-col justify-center items-center">
                    <div className="text-5xl font-bold text-accent-warning mb-2">{overview?.superpositions?.length || 0}</div>
                    <div className="text-sm text-text-secondary uppercase tracking-widest text-center">Parallel Reasoning Threads</div>
                  </div>
                </div>
              </div>

              <div className="panel flex-1">
                <div className="panel-header">
                  <h2 className="panel-title">Resource Utilization History</h2>
                  <Cpu className="panel-icon" size={18} />
                </div>
                <div className="panel-body">
                  <div className="space-y-6">
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-text-secondary">Collective CPU Core Utilization</span>
                        <span className="text-accent-primary font-mono">{overview?.system?.cpu_load?.toFixed(1) || 0}%</span>
                      </div>
                      <div className="w-full bg-background-primary rounded-full h-4 overflow-hidden border border-border-color">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${overview?.system?.cpu_load || 0}%` }}
                          className="bg-accent-primary h-full shadow-[0_0_10px_rgba(0,170,255,0.5)]"
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-text-secondary">Distributed Memory Pressure</span>
                        <span className="text-accent-success font-mono">{overview?.system?.memory_usage?.toFixed(1) || 0}%</span>
                      </div>
                      <div className="w-full bg-background-primary rounded-full h-4 overflow-hidden border border-border-color">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${overview?.system?.memory_usage || 0}%` }}
                          className="bg-accent-success h-full shadow-[0_0_10px_rgba(0,255,65,0.5)]"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* 08 FEDERATION */}
          {activeTab === 'federation' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Federation Control</h1>
              {federationData.stats?.error ? (
                <div className="panel flex-1 flex flex-col items-center justify-center p-12 text-center">
                  <XCircle size={64} className="text-accent-danger mb-4 opacity-50" />
                  <h2 className="text-2xl font-bold mb-2 text-text-primary">Federated Mesh Inactive</h2>
                  <p className="text-text-secondary max-w-md">The federation service is currently waiting for secondary nodes or has not been initialized on this instance. Check logs for SEED_NODE connectivity.</p>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="stat-card">
                      <div className="flex items-center justify-between">
                        <span className="stat-card-label">Active Peers</span>
                        <Users className="stat-card-icon" size={20} />
                      </div>
                      <div className="stat-card-value">{federationData.stats?.connected_nodes || 0}</div>
                    </div>
                    <div className="stat-card">
                      <div className="flex items-center justify-between">
                        <span className="stat-card-label">Total Shared Nodes</span>
                        <Package className="stat-card-icon" size={20} />
                      </div>
                      <div className="stat-card-value">{federationData.stats?.total_nodes || 0}</div>
                    </div>
                    <div className="stat-card">
                      <div className="flex items-center justify-between">
                        <span className="stat-card-label">Local Node</span>
                        <Server className="stat-card-icon" size={20} />
                      </div>
                      <div className="text-xs font-mono text-accent-primary truncate">{federationData.stats?.local_node?.node_id || "OFFLINE"}</div>
                    </div>
                  </div>
                  <div className="panel flex-1">
                    <div className="panel-header">
                      <h2 className="panel-title">Federated Peers</h2>
                      <Server className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body overflow-x-auto">
                      <table className="data-table">
                        <thead className="data-table-header">
                          <tr>
                            <th>Peer Name</th>
                            <th>Status</th>
                            <th>Last Seen</th>
                            <th>Host/Port</th>
                            <th>Capabilities</th>
                          </tr>
                        </thead>
                        <tbody className="data-table-body">
                          {federationData.peers && federationData.peers.length > 0 ? federationData.peers.map(peer => (
                            <tr key={peer.node_id} className="data-table-row">
                              <td className="font-bold">{peer.name}</td>
                              <td><div className={`tag ${peer.status === 'online' ? 'tag-success' : 'tag-danger'}`}>{peer.status}</div></td>
                              <td className="text-xs font-mono">{peer.last_seen ? new Date(peer.last_seen).toLocaleString() : 'N/A'}</td>
                              <td className="text-xs font-mono">{peer.host}:{peer.port}</td>
                              <td>
                                <div className="flex gap-1">
                                  {peer.capabilities?.slice(0, 2).map(c => <span key={c} className="tag-xs">{c}</span>)}
                                </div>
                              </td>
                            </tr>
                          )) : (
                            <tr><td colSpan="5" className="text-center py-12 text-text-secondary opacity-50">No external peers discovered on the mesh.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          )}

          {/* 09 SECURITY */}
          {activeTab === 'security' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Sentinel Neural Wall</h1>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="stat-card">
                  <div className="flex items-center justify-between">
                    <span className="stat-card-label">Threats Detected</span>
                    <Shield className="stat-card-icon" size={20} />
                  </div>
                  <div className="stat-card-value">{securityData.stats?.threats_detected_24h || 0}</div>
                </div>
                <div className="stat-card">
                  <div className="flex items-center justify-between">
                    <span className="stat-card-label">Threats Neutralized</span>
                    <CheckCircle2 className="stat-card-icon" size={20} />
                  </div>
                  <div className="stat-card-value">{securityData.stats?.threats_neutralized_24h || 0}</div>
                </div>
              </div>
              <div className="panel flex-1">
                <div className="panel-header">
                  <h2 className="panel-title">Threat Log</h2>
                  <Activity className="panel-icon" size={18} />
                </div>
                <div className="panel-body">
                  <table className="data-table">
                    <thead className="data-table-header">
                      <tr>
                        <th>Timestamp</th>
                        <th>Threat Type</th>
                        <th>Severity</th>
                        <th>Action Taken</th>
                        <th>Source</th>
                      </tr>
                    </thead>
                    <tbody className="data-table-body">
                      {securityData.threats.map(threat => (
                        <tr key={threat.id} className="data-table-row">
                          <td>{new Date(threat.timestamp).toLocaleString()}</td>
                          <td>{threat.threat_type}</td>
                          <td><div className={`tag ${threat.severity === 'critical' ? 'tag-danger' : threat.severity === 'high' ? 'tag-warning' : 'tag-info'}`}>{threat.severity}</div></td>
                          <td>{threat.action_taken}</td>
                          <td>{threat.source_ip}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          )}

          {/* 10 RESEARCH */}
          {activeTab === 'research' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Autonomous Research</h1>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="stat-card">
                  <span className="stat-card-label">Active Tasks</span>
                  <div className="stat-card-value">{researchData.stats?.active_tasks || 0}</div>
                </div>
                <div className="stat-card">
                  <span className="stat-card-label">Completed Tasks</span>
                  <div className="stat-card-value">{researchData.stats?.completed_tasks_24h || 0}</div>
                </div>
              </div>
              <div className="panel flex-1">
                <div className="panel-header">
                  <h2 className="panel-title">Research Tasks</h2>
                </div>
                <div className="panel-body">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {researchData.tasks.map(task => (
                      <div key={task.task_id} className="card">
                        <div className="font-bold">{task.objective}</div>
                        <div className="text-sm text-text-secondary">{task.status}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* 11 VERIFICATION */}
          {activeTab === 'verification' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Chain of Verification</h1>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="stat-card">
                  <span className="stat-card-label">Items in Queue</span>
                  <div className="stat-card-value">{verificationData.stats?.items_in_queue || 0}</div>
                </div>
                <div className="stat-card">
                  <span className="stat-card-label">Verified Last Hour</span>
                  <div className="stat-card-value">{verificationData.stats?.verified_last_hour || 0}</div>
                </div>
              </div>
              <div className="panel flex-1">
                <div className="panel-header">
                  <h2 className="panel-title">Verification Queue</h2>
                </div>
                <div className="panel-body">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {verificationData.queue.map(item => (
                      <div key={item.item_id} className="card">
                        <div className="font-bold">{item.item_type}</div>
                        <div className="text-sm text-text-secondary">Status: {item.status}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* 12 INFRASTRUCTURE */}
          {activeTab === 'infra' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Self-Healing Infrastructure</h1>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="stat-card">
                  <span className="stat-card-label">Node Status</span>
                  <div className="stat-card-value">{infraData.status?.overall_status || 'Unknown'}</div>
                </div>
                <div className="stat-card">
                  <span className="stat-card-label">Active Nodes</span>
                  <div className="stat-card-value">{infraData.status?.active_nodes || 0}</div>
                </div>
              </div>
              <div className="panel flex-1">
                <div className="panel-header">
                  <h2 className="panel-title">Node Status</h2>
                </div>
                <div className="panel-body">
                  <table className="data-table">
                    <thead className="data-table-header">
                      <tr>
                        <th>Node ID</th>
                        <th>Status</th>
                        <th>CPU</th>
                        <th>Memory</th>
                      </tr>
                    </thead>
                    <tbody className="data-table-body">
                      {infraData.nodes.map(node => (
                        <tr key={node.node_id} className="data-table-row">
                          <td>{node.node_id}</td>
                          <td>{node.status}</td>
                          <td>{node.cpu_usage}%</td>
                          <td>{node.memory_usage}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          )}

          {/* 13 TESTING */}
          {activeTab === 'testing' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Zero-Human Testing</h1>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="stat-card">
                  <span className="stat-card-label">Tests Running</span>
                  <div className="stat-card-value">{testingData.stats?.tests_running || 0}</div>
                </div>
                <div className="stat-card">
                  <span className="stat-card-label">Success Rate (24h)</span>
                  <div className="stat-card-value">{testingData.stats?.success_rate_24h || 0}%</div>
                </div>
              </div>
              <div className="panel flex-1">
                <div className="panel-header">
                  <h2 className="panel-title">Test Runs</h2>
                </div>
                <div className="panel-body">
                  <table className="data-table">
                    <thead className="data-table-header">
                      <tr>
                        <th>Run ID</th>
                        <th>Status</th>
                        <th>Timestamp</th>
                        <th>Duration</th>
                      </tr>
                    </thead>
                    <tbody className="data-table-body">
                      {testingData.runs.map(run => (
                        <tr key={run.run_id} className="data-table-row">
                          <td>{run.run_id}</td>
                          <td>{run.status}</td>
                          <td>{new Date(run.timestamp).toLocaleString()}</td>
                          <td>{run.duration_seconds}s</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          )}

          {/* 14 KANBAN BOARD */}
          {activeTab === 'kanban' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <div className="flex justify-between items-end">
                <h1 className="section-title">Vibe Kanban // Task Orchestration</h1>
                <div className="flex items-center gap-4">
                  <div className="tag tag-success">{kanbanStats.total_cards || 0} Cards</div>
                  <div className="tag">{kanbanStats.in_progress_count || 0} Active</div>
                </div>
              </div>

              {/* Card Creator */}
              <div className="panel">
                <div className="panel-header">
                  <h2 className="panel-title">Create Task Card</h2>
                  <Plus className="panel-icon" size={18} />
                </div>
                <div className="panel-body flex gap-4 items-end">
                  <input value={newCardTitle} onChange={e => setNewCardTitle(e.target.value)} placeholder="Task title..." className="input-field flex-1" />
                  <input value={newCardAssignee} onChange={e => setNewCardAssignee(e.target.value)} placeholder="Assignee (agent)" className="input-field" style={{ maxWidth: 180 }} />
                  <select value={newCardPriority} onChange={e => setNewCardPriority(e.target.value)} className="input-field" style={{ maxWidth: 140 }}>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                  <button className="button-primary" disabled={!newCardTitle.trim()} onClick={async () => {
                    await axios.post(`${API_BASE}/kanban/cards`, { title: newCardTitle, assignee: newCardAssignee, priority: newCardPriority });
                    setNewCardTitle(''); setNewCardAssignee('');
                    const [b, s] = await Promise.all([fetch(`${API_BASE}/kanban/board`).then(r => r.json()), fetch(`${API_BASE}/kanban/stats`).then(r => r.json())]);
                    setKanbanBoard(b); setKanbanStats(s);
                  }}>
                    <Plus size={16} /><span>Create</span>
                  </button>
                </div>
              </div>

              {/* Kanban Columns */}
              <div className="grid grid-cols-4 gap-4 flex-1 min-h-0">
                {['TODO', 'IN_PROGRESS', 'REVIEW', 'DONE'].map(col => (
                  <div key={col} className="panel flex flex-col min-h-0">
                    <div className="panel-header">
                      <h2 className="panel-title text-xs">{col.replace('_', ' ')}</h2>
                      <div className="tag text-[8px]">{(kanbanBoard[col] || []).length}</div>
                    </div>
                    <div className="panel-body flex-1 overflow-y-auto custom-scrollbar" style={{ maxHeight: 500 }}>
                      <div className="space-y-2">
                        {(kanbanBoard[col] || []).map(card => (
                          <div key={card.card_id} className="card-secondary">
                            <div className="flex justify-between items-start mb-1">
                              <span className="font-bold text-sm">{card.title}</span>
                              <div className={`tag text-[7px] px-1 ${card.priority === 'critical' ? 'tag-danger' : card.priority === 'high' ? 'tag-warning' : 'tag-info'
                                }`}>{card.priority}</div>
                            </div>
                            {card.assignee && <div className="text-[9px] text-text-secondary">Agent: <span className="text-accent-primary">{card.assignee}</span></div>}
                            {card.allocated_port > 0 && <div className="text-[9px] text-text-secondary">Port: {card.allocated_port}</div>}
                            <div className="flex gap-1 mt-2">
                              {col === 'TODO' && <button className="glass-button text-[8px] py-0.5 px-2" onClick={async () => {
                                await axios.post(`${API_BASE}/kanban/cards/${card.card_id}/move`, { target_status: 'IN_PROGRESS' });
                                const b = await fetch(`${API_BASE}/kanban/board`).then(r => r.json()); setKanbanBoard(b);
                              }}>▶ Start</button>}
                              {col === 'IN_PROGRESS' && <button className="glass-button text-[8px] py-0.5 px-2" onClick={async () => {
                                await axios.post(`${API_BASE}/kanban/cards/${card.card_id}/move`, { target_status: 'REVIEW' });
                                const b = await fetch(`${API_BASE}/kanban/board`).then(r => r.json()); setKanbanBoard(b);
                              }}>⏫ Review</button>}
                              {col === 'REVIEW' && <>
                                <button className="glass-button text-[8px] py-0.5 px-2" style={{ color: '#22c55e' }} onClick={async () => {
                                  await axios.post(`${API_BASE}/kanban/cards/${card.card_id}/move`, { target_status: 'DONE' });
                                  const b = await fetch(`${API_BASE}/kanban/board`).then(r => r.json()); setKanbanBoard(b);
                                }}>✓ Done</button>
                                <button className="glass-button text-[8px] py-0.5 px-2" style={{ color: '#f97316' }} onClick={async () => {
                                  await axios.post(`${API_BASE}/kanban/cards/${card.card_id}/move`, { target_status: 'IN_PROGRESS' });
                                  const b = await fetch(`${API_BASE}/kanban/board`).then(r => r.json()); setKanbanBoard(b);
                                }}>↩ Rework</button>
                              </>}
                            </div>
                          </div>
                        ))}
                        {(kanbanBoard[col] || []).length === 0 && (
                          <div className="text-center py-8 text-text-secondary opacity-30 text-[10px] font-mono">EMPTY</div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* 15 DDR & VAULT */}
          {activeTab === 'ddr' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Digital DNA Repository & Secrets Vault</h1>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="stat-card">
                  <div className="flex items-center justify-between"><span className="stat-card-label">Total Antibodies</span><ShieldAlert className="stat-card-icon" size={20} /></div>
                  <div className="stat-card-value">{ddrStats.total_antibodies || 0}</div>
                </div>
                <div className="stat-card">
                  <div className="flex items-center justify-between"><span className="stat-card-label">Errors Prevented</span><Bug className="stat-card-icon" size={20} /></div>
                  <div className="stat-card-value">{ddrStats.total_prevented || 0}</div>
                </div>
                <div className="stat-card">
                  <div className="flex items-center justify-between"><span className="stat-card-label">Vault Keys</span><KeyRound className="stat-card-icon" size={20} /></div>
                  <div className="stat-card-value">{secretKeys.length}</div>
                </div>
                <div className="stat-card">
                  <div className="flex items-center justify-between"><span className="stat-card-label">Last Scan</span><Scan className="stat-card-icon" size={20} /></div>
                  <div className="stat-card-value text-sm">{ddrStats.last_scan || 'Never'}</div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0">
                {/* Antibody List */}
                <div className="panel flex flex-col min-h-0">
                  <div className="panel-header">
                    <h2 className="panel-title">Active Antibodies</h2>
                    <ShieldAlert className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body flex-1 overflow-y-auto custom-scrollbar" style={{ maxHeight: 400 }}>
                    {ddrAntibodies.map((ab, i) => (
                      <div key={ab.error_type + '-' + i} className="card-secondary mb-2">
                        <div className="flex justify-between items-start">
                          <span className="font-bold text-sm text-accent-danger">{ab.error_type}</span>
                          <div className={`tag text-[7px] ${ab.severity === 'critical' ? 'tag-danger' : ab.severity === 'high' ? 'tag-warning' : 'tag-info'}`}>
                            {ab.severity || 'medium'}
                          </div>
                        </div>
                        <p className="text-xs text-text-secondary mt-1">{ab.fix}</p>
                        {ab.pattern && <div className="text-[9px] font-mono text-accent-primary/60 mt-1">Pattern: {ab.pattern}</div>}
                      </div>
                    ))}
                    {ddrAntibodies.length === 0 && <div className="text-center py-8 text-text-secondary opacity-40">No antibodies registered</div>}
                  </div>
                </div>

                {/* Code Scanner + Vault */}
                <div className="flex flex-col gap-4">
                  <div className="panel">
                    <div className="panel-header">
                      <h2 className="panel-title">Code Scanner</h2>
                      <Scan className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body">
                      <textarea value={ddrScanCode} onChange={e => setDdrScanCode(e.target.value)}
                        placeholder='Paste code to scan for vulnerabilities...\ne.g. query = f"SELECT * FROM users WHERE id={user_id}"'
                        rows="4" className="input-field font-mono w-full" />
                    </div>
                    <div className="panel-footer">
                      <button className="button-primary" disabled={!ddrScanCode.trim()} onClick={async () => {
                        const res = await axios.post(`${API_BASE}/ddr/scan`, { code: ddrScanCode });
                        setDdrScanResult(res.data);
                      }}>
                        <Scan size={16} /><span>Scan Code</span>
                      </button>
                    </div>
                    {ddrScanResult && (
                      <div className="p-4 border-t border-border-color">
                        <div className="text-xs font-bold mb-2">
                          {ddrScanResult.matches?.length > 0
                            ? <span className="text-accent-danger">⚠ {ddrScanResult.matches.length} vulnerabilities found</span>
                            : <span className="text-accent-success">✓ No known vulnerabilities detected</span>}
                        </div>
                        {ddrScanResult.matches?.map((m, i) => (
                          <div key={i} className="text-[10px] font-mono text-accent-danger/80 mb-1">
                            [{m.error_type}] {m.fix}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="panel">
                    <div className="panel-header">
                      <h2 className="panel-title">Secrets Vault</h2>
                      <KeyRound className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body">
                      {secretKeys.length > 0 ? secretKeys.map(k => (
                        <div key={k} className="flex items-center gap-2 py-1 border-b border-border-color">
                          <Lock size={12} className="text-accent-warning" />
                          <span className="font-mono text-sm">{k}</span>
                          <span className="text-[9px] text-text-secondary ml-auto">ENCRYPTED</span>
                        </div>
                      )) : (
                        <div className="text-center py-6 text-text-secondary opacity-40 text-sm">Vault empty — no secrets stored</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* 16 AGENT COMMS */}
          {activeTab === 'comms' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Agent Communications & Missions</h1>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0">
                {/* Mailbox */}
                <div className="panel flex flex-col min-h-0">
                  <div className="panel-header">
                    <h2 className="panel-title">Agent Mailboxes</h2>
                    <Inbox className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body">
                    <div className="space-y-1 mb-4">
                      {mailboxAgents.map(agent => (
                        <button key={agent} className={`w-full text-left px-3 py-2 rounded-lg text-sm font-mono transition-all ${selectedMailbox === agent ? 'bg-accent-primary/20 text-accent-primary border border-accent-primary/30' : 'hover:bg-white/5 text-text-secondary'
                          }`} onClick={async () => {
                            setSelectedMailbox(agent);
                            const res = await fetch(`${API_BASE}/mailbox/${agent}/inbox`).then(r => r.json());
                            setMailboxMessages(res.messages || []);
                          }}>
                          <Mail size={12} className="inline mr-2" />{agent}
                        </button>
                      ))}
                      {mailboxAgents.length === 0 && <div className="text-center py-4 text-text-secondary opacity-40 text-xs">No mailboxes found</div>}
                    </div>

                    {selectedMailbox && (
                      <div className="border-t border-border-color pt-3">
                        <div className="text-[9px] font-mono text-text-secondary uppercase mb-2">Inbox: {selectedMailbox} ({mailboxMessages.length} msgs)</div>
                        <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                          {mailboxMessages.map((msg, i) => (
                            <div key={i} className="card-secondary text-[10px]">
                              <div className="font-bold">{msg.subject || '(no subject)'}</div>
                              <div className="text-text-secondary">{msg.body?.slice(0, 100)}</div>
                              <div className="text-[8px] text-accent-primary mt-1">From: {msg.from}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Send Message */}
                  <div className="panel-footer flex-col gap-2">
                    <div className="text-[9px] font-mono text-text-secondary uppercase">Send Message</div>
                    <input value={sendMsgFrom} onChange={e => setSendMsgFrom(e.target.value)} placeholder="From agent" className="input-field text-xs" />
                    <input value={sendMsgTo} onChange={e => setSendMsgTo(e.target.value)} placeholder="To agent" className="input-field text-xs" />
                    <textarea value={sendMsgBody} onChange={e => setSendMsgBody(e.target.value)} placeholder="Message body..." rows="2" className="input-field text-xs" />
                    <button className="button-primary w-full justify-center" disabled={!sendMsgTo.trim() || !sendMsgBody.trim()} onClick={async () => {
                      await axios.post(`${API_BASE}/mailbox/send`, { from_agent: sendMsgFrom, to_agent: sendMsgTo, body: sendMsgBody, subject: 'Dashboard Message' });
                      setSendMsgBody(''); setSendMsgTo('');
                    }}>
                      <Send size={14} /><span>Send</span>
                    </button>
                  </div>
                </div>

                {/* Ultrawork Missions */}
                <div className="panel flex flex-col min-h-0">
                  <div className="panel-header">
                    <h2 className="panel-title">Ultrawork Missions</h2>
                    <Rocket className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body flex-1 overflow-y-auto custom-scrollbar">
                    {uwMissions.length > 0 ? uwMissions.map(m => (
                      <div key={m.mission_id} className="card-secondary mb-2">
                        <div className="flex justify-between items-start">
                          <span className="font-bold text-sm">{m.objective}</span>
                          <div className={`tag text-[7px] ${m.phase === 'completed' ? 'tag-success' : m.phase === 'acting' ? 'tag-warning' : 'tag-info'
                            }`}>{m.phase}</div>
                        </div>
                        <div className="text-[9px] text-text-secondary mt-1">ID: {m.mission_id}</div>
                        {m.attempt > 1 && <div className="text-[9px] text-accent-warning">Attempt #{m.attempt}</div>}
                      </div>
                    )) : (
                      <div className="text-center py-12 text-text-secondary opacity-40">
                        <Rocket size={32} className="mx-auto mb-2" />
                        <p className="text-xs">No active missions</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Portable Skills */}
                <div className="panel flex flex-col min-h-0">
                  <div className="panel-header">
                    <h2 className="panel-title">Portable Skills (SKILL.md)</h2>
                    <BookOpen className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body flex-1 overflow-y-auto custom-scrollbar">
                    {portableSkills.length > 0 ? portableSkills.map(s => (
                      <div key={s.name} className="card-secondary mb-2">
                        <div className="flex justify-between items-start">
                          <span className="font-bold text-sm">{s.name}</span>
                          <div className={`tag text-[7px] ${s.source === 'skill_md' ? 'tag-success' : 'tag-info'}`}>
                            {s.source === 'skill_md' ? 'SKILL.md' : 'Python'}
                          </div>
                        </div>
                        <p className="text-xs text-text-secondary mt-1">{s.description}</p>
                      </div>
                    )) : (
                      <div className="text-center py-12 text-text-secondary opacity-40">
                        <BookOpen size={32} className="mx-auto mb-2" />
                        <p className="text-xs">No skills discovered</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </main>
    </div>
  );
}
