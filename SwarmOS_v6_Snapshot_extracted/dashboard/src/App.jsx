import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = 'http://localhost:8001';
import {
  Terminal, Cpu, Activity, RefreshCw, MessageSquare, Users, Send,
  Shield, Zap, ChevronRight, Lock, Boxes, GitBranch, Play, X, Plus,
  Loader2, CheckCircle2, Brain, FileText, XCircle, ArrowRight,
  TestTube, Package, Eye, Check, Ban, RotateCcw, Rocket, ScrollText,
  BookOpen, Sparkles, Trash2, Upload, GraduationCap, Network, Database,
  Wrench, Globe, Radio, Orbit, LayoutDashboard, Layers,
  Beaker, GitMerge, Server
} from 'lucide-react';
import axios from 'axios';
import MeshHeatmap from './components/MeshHeatmap';

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

  const chatEndRef = useRef(null);

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

        const dataPromises = endpoints.map(e => fetch(`${API_BASE}${e.url}`).then(res => res.json()));
        const [expertsData, artifactsData, resourcesData, meshData, skillsData, memData, telemetryData] = await Promise.all(dataPromises);

        setExperts(expertsData);
        if (expertsData.length > 0 && !selectedRole) setSelectedRole(expertsData[0].role);
        setArtifacts(artifactsData.artifacts);
        setArtStats(artifactsData.stats);
        setResources(resourcesData);
        setMeshTopology(meshData);
        setLearnedSkills(skillsData.skills || []);
        setMemStats(memData);
        setOverview(telemetryData);

      } catch (err) { console.error("Sync Error", err); }
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
        }
      } catch (error) {
        console.error(`Error fetching data for tab ${tab}:`, error);
      }
    };

    fetchData(); // Initial global fetch
    fetchTabData(activeTab); // Initial fetch for the active tab

    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [selectedRole, activeTab]);

  useEffect(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages, selectedRole]);

  const sendMessage = async () => {
    if (!inputMsg.trim() || !selectedRole || isProcessing) return;
    const role = selectedRole;
    setMessages(prev => ({ ...prev, [role]: [...(prev[role] || []), { text: inputMsg, sender: 'user', time: new Date().toLocaleTimeString() }] }));
    setInputMsg('');
    setIsProcessing(true);
    try {
      console.log('Sending message:', { role, message: inputMsg });
      const res = await axios.post(`${API_BASE}/swarm/chat`, { role, message: inputMsg });
      console.log('Received response:', res.data);
      setMessages(prev => ({ ...prev, [role]: [...(prev[role] || []), { text: res.data.response, sender: 'agent', name: res.data.name, time: new Date().toLocaleTimeString() }] }));
    } catch (err) {
      console.error('Chat Error:', err);
      setMessages(prev => ({ ...prev, [role]: [...(prev[role] || []), { text: '⚠️ [NEURAL_LINK_STALLED]', sender: 'system' }] }));
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

                {/* Column 3: Active Superpositions */}
                <div className="col-span-1 panel">
                  <div className="panel-header">
                    <h2 className="panel-title">Active Superpositions</h2>
                    <GitMerge className="panel-icon" size={18} />
                  </div>
                  <div className="panel-body space-y-2">
                    {overview?.superpositions?.map((sup, i) => (
                      <div key={i} className="card-secondary">
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
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full">
              <h1 className="section-title">Neural Bridge</h1>

              <div className="flex items-center gap-2 mb-4">
                {experts.map(e => (
                  <button key={e.role} onClick={() => setSelectedRole(e.role)}
                    className={`chip-button ${selectedRole === e.role ? 'active' : ''}`}>
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: e.avatar_color }}/>
                    <span>{e.name}</span>
                  </button>
                ))}
              </div>

              <div className="panel flex-1 flex flex-col col-span-12">
                <div className="panel-header">
                  <h2 className="panel-title">Commlink // {selectedRole?.toUpperCase()}</h2>
                  <div className="flex items-center gap-2 text-xs text-accent-success">
                    <div className="w-2 h-2 rounded-full bg-accent-success animate-pulse" />
                    <span>Link Active</span>
                  </div>
                </div>

                <div className="panel-body flex-1 space-y-4">
                  {(messages[selectedRole] || []).map((msg, i) => (
                    <div key={i} className={`chat-message ${msg.sender === 'user' ? 'user' : 'agent'}`}>
                      <div className="chat-bubble">
                        {msg.text}
                        <div className="chat-timestamp">{msg.time} // {msg.sender === 'agent' ? msg.name : 'USER'}</div>
                      </div>
                    </div>
                  ))}
                  {isProcessing && <div className="chat-message agent"><div className="chat-bubble"><Loader2 className="animate-spin" size={16} /></div></div>}
                  <div ref={chatEndRef} />
                </div>

                <div className="panel-footer">
                  <input value={inputMsg} onChange={e => setInputMsg(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()}
                    placeholder="Transmit neural command..." className="input-field" />
                  <button onClick={sendMessage} className="button-primary">
                    <Send size={16} />
                    <span>Transmit</span>
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* 03 SWARM INTEL */}
          {activeTab === 'intel' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Shared Intel Reservoir</h1>
              <div className="panel-grid panel-grid-3-col">
                {/* Left Column */}
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
                        {(memoryStats.types && Object.entries(memoryStats.types).map(([type, count]) => (
                          <div key={type} className="card-secondary text-center">
                            <div className="font-bold text-sm">{type}</div>
                            <div className="text-lg">{count}</div>
                          </div>
                        ))) || <p>No types.</p>}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Middle Column: Query */}
                <div className="col-span-1 flex flex-col gap-4">
                  <div className="panel flex-1">
                    <div className="panel-header">
                      <h2 className="panel-title">Query Interface</h2>
                      <FileText className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body flex flex-col gap-4">
                      <textarea value={memQuery} onChange={e => setMemQuery(e.target.value)} placeholder="Query the collective memory..." className="input-field flex-1" />
                    </div>
                    <div className="panel-footer">
                      <button onClick={queryMemory} disabled={isQuerying} className="button-primary w-full justify-center">
                        {isQuerying ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
                        <span>{isQuerying ? 'Querying...' : 'Query Memory'}</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Right Column: Results */}
                <div className="col-span-1 flex flex-col gap-4">
                  <div className="panel flex-1">
                    <div className="panel-header">
                      <h2 className="panel-title">Query Results</h2>
                      <Sparkles className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body space-y-2">
                      {memResults.length > 0 ? memResults.map((res, i) => (
                        <div key={i} className="card-secondary">
                          <p className="text-sm">{res.content}</p>
                          <p className="text-xs text-text-secondary mt-2">Dist: {res.distance.toFixed(4)} | ID: {res.id}</p>
                        </div>
                      )) : <p className="text-sm text-text-secondary">No results.</p>}
                    </div>
                  </div>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(memoryStats.by_type || {}).map(([type, count]) => (
                          <div key={type} className="card-secondary items-center">
                            <div className="font-bold text-accent-primary text-xl">{count}</div>
                            <div className="text-xs text-text-secondary uppercase">{type}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Column */}
                <div className="lg:col-span-2 panel flex flex-col">
                  <div className="panel-header">
                    <h2 className="panel-title">Neural Repository Query</h2>
                    <Globe className="panel-icon" size={18} />
                  </div>
                  <div className="panel-footer">
                     <input value={memQuery} onChange={e => setMemQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && queryMemory()}
                      placeholder="Query the collective neural repository..." className="input-field" />
                    <button onClick={queryMemory} disabled={isQuerying} className="button-primary">
                      {isQuerying ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
                      <span>{isQuerying ? 'Querying...' : 'Query'}</span>
                    </button>
                  </div>
                  {memResults.length > 0 && (
                    <div className="panel-body">
                      {memResults.map((r, i) => (
                        <div key={i} className="card-secondary">
                          <div className="flex justify-between items-start">
                            <p className="text-sm text-text-primary font-mono">{r.memory}</p>
                            <div className="tag whitespace-nowrap">{(r.match_percentage * 100).toFixed(0)}%</div>
                          </div>
                          <p className="text-xs text-text-secondary mt-2">Source: {r.source}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
            )}

          {/* 04 ARTIFACT FLOW */}
          {activeTab === 'pipeline' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Autonomous Pipeline</h1>
              <div className="panel-grid panel-grid-12-col">
                  {/* Left Column */}
                  <div className="col-span-4 flex flex-col gap-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="stat-card">
                      <div className="stat-card-label">Total</div>
                      <div className="stat-card-value">{artStats.total || 0}</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-card-label">Pending</div>
                      <div className="stat-card-value text-accent-warning">{artStats.pending || 0}</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-card-label">Approved</div>
                      <div className="stat-card-value text-accent-success">{artStats.approved || 0}</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-card-label">Rejected</div>
                      <div className="stat-card-value text-accent-danger">{artStats.rejected || 0}</div>
                    </div>
                  </div>
                    <div className="panel flex-1">
                    <div className="panel-header">
                      <h2 className="panel-title">Review Queue</h2>
                      <Layers className="panel-icon" size={18} />
                    </div>
                    <div className="panel-body">
                      {artifacts.filter(a => a.status === 'pending').map(a => (
                        <button key={a.filename} onClick={() => setSelectedArtifact(a)} 
                          className={`card-secondary w-full text-left ${selectedArtifact?.filename === a.filename ? 'active' : ''}`}>
                          <div className="flex justify-between items-center">
                            <span className="font-mono text-sm truncate">{a.filename}</span>
                            <div className="tag">{a.type}</div>
                          </div>
                          <div className="text-xs text-text-secondary mt-1">Created by: {a.agent}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Column */}
                <div className="col-span-8 panel flex flex-col">
                  {selectedArtifact ? (
                    <>
                      <div className="panel-header">
                        <h2 className="panel-title font-mono truncate">{selectedArtifact.filename}</h2>
                        <div className="flex items-center gap-4">
                          <div className="tag">{selectedArtifact.type}</div>
                          <div className="tag">{selectedArtifact.status}</div>
                          <button onClick={() => setSelectedArtifact(null)} className="text-text-secondary hover:text-text-primary">
                            <X size={18} />
                          </button>
                        </div>
                      </div>
                      <div className="panel-body flex-1 bg-background-primary font-mono text-xs overflow-auto custom-scrollbar">
                        <pre><code className="language-js">{selectedArtifact.content}</code></pre>
                      </div>
                      <div className="panel-footer">
                        <button onClick={() => handleArtifactAction(selectedArtifact.filename, 'reject')} className="button-danger">
                          <Ban size={16} /><span>Reject</span>
                        </button>
                        <div className="flex-grow" />
                        <button onClick={() => handleArtifactAction(selectedArtifact.filename, 'test')} className="button-secondary">
                          <Beaker size={16} /><span>Test</span>
                        </button>
                        <button onClick={() => handleArtifactAction(selectedArtifact.filename, 'approve')} className="button-success">
                          <Check size={16} /><span>Approve</span>
                        </button>
                        <button onClick={() => handleArtifactAction(selectedArtifact.filename, 'integrate')} className="button-primary">
                          <GitMerge size={16} /><span>Integrate</span>
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="panel-body flex items-center justify-center text-text-secondary">
                      <div className="text-center">
                        <Package size={48} className="mx-auto mb-2" />
                        <h3 className="text-lg font-bold">Select an artifact to review</h3>
                        <p>Pending artifacts will appear in the queue on the left.</p>
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
                    <button onClick={() => {}} disabled={isLearning} className="button-primary">
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
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
              <h1 className="section-title">Real-Time Telemetry</h1>
              {/* Placeholder for Telemetry content */}
            </motion.div>
          )}

          {/* 08 FEDERATION */}
          {activeTab === 'federation' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <h1 className="section-title">Federation Control</h1>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="stat-card">
                  <div className="flex items-center justify-between">
                    <span className="stat-card-label">Active Peers</span>
                    <Users className="stat-card-icon" size={20} />
                  </div>
                  <div className="stat-card-value">{federationData.stats?.active_peers || 0}</div>
                </div>
                <div className="stat-card">
                  <div className="flex items-center justify-between">
                    <span className="stat-card-label">Total Data Shared</span>
                    <Package className="stat-card-icon" size={20} />
                  </div>
                  <div className="stat-card-value">{((federationData.stats?.total_data_shared_mb || 0)).toFixed(2)} MB</div>
                </div>
              </div>
              <div className="panel flex-1">
                <div className="panel-header">
                  <h2 className="panel-title">Federated Peers</h2>
                  <Server className="panel-icon" size={18} />
                </div>
                <div className="panel-body">
                  <table className="data-table">
                    <thead className="data-table-header">
                      <tr>
                        <th>Peer ID</th>
                        <th>Status</th>
                        <th>Last Sync</th>
                        <th>Data Shared</th>
                      </tr>
                    </thead>
                    <tbody className="data-table-body">
                      {federationData.peers.map(peer => (
                        <tr key={peer.peer_id} className="data-table-row">
                          <td>{peer.peer_id}</td>
                          <td><div className={`tag ${peer.status === 'online' ? 'tag-success' : 'tag-danger'}`}>{peer.status}</div></td>
                          <td>{new Date(peer.last_sync).toLocaleString()}</td>
                          <td>{peer.data_shared_mb.toFixed(2)} MB</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
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
        </AnimatePresence>
      </main>
    </div>
  );
}
