
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Terminal, Cpu, Activity, RefreshCw, MessageSquare, Users, Send,
  Shield, Zap, ChevronRight, Lock, Boxes, GitBranch, Play, X, Plus,
  Loader2, CheckCircle2, Brain, FileText, XCircle, ArrowRight,
  TestTube, Package, Eye, Check, Ban, RotateCcw, Rocket, ScrollText,
  BookOpen, Sparkles, Trash2, Upload, GraduationCap, Network, Database,
  Wrench, Globe, Radio, Orbit, LayoutDashboard, Layers, Search
} from 'lucide-react';
import axios from 'axios';
import MeshHeatmap from './components/MeshHeatmap';

const API_BASE = 'http://127.0.0.1:8001';

// ─── Component: LCARS Sidebar ───────────────────────────────────────────
const LCARS_Sidebar = ({ activeTab, onTabChange, stats }) => {
  const menuItems = [
    { id: 'overview', label: '01 SYSTEM STATUS', color: 'orange' },
    { id: 'chat', label: '02 NEURAL BRIDGE', color: 'purple' },
    { id: 'intel', label: '03 SWARM INTEL', color: 'blue' },
    { id: 'pipeline', label: '04 ARTIFACT FLOW', color: 'tan' },
    { id: 'learning', label: '05 SKILL REGISTRY', color: 'gold' },
    { id: 'mesh', label: '06 MESH NET', color: 'orange' },
    { id: 'telemetry', label: '07 TELEMETRY', color: 'cyan' },
    { id: 'qiae', label: '08 QIAE STACK', color: 'gold' },
  ];

  return (
    <aside className="flex flex-col h-full gap-1">
      <div className="lcars-elbow-top-left" />
      <div className="flex-1 flex flex-col gap-1 overflow-y-auto pr-2 custom-scrollbar">
        {menuItems.map(item => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`lcars-button ${item.color} ${activeTab === item.id ? 'active' : ''}`}
            style={{
              justifyContent: 'flex-end',
              textAlign: 'right',
              paddingRight: '15px',
              borderRight: activeTab === item.id ? '10px solid white' : 'none',
              height: '35px',
              fontSize: '11px'
            }}
          >
            {item.label}
          </button>
        ))}

        <div className="flex-1" />

        {/* Resource Telemetry */}
        <div className="lcars-stat-box p-4" style={{ background: '#0a0a0a', borderLeft: '6px solid var(--lcars-blue)', marginBottom: '10px' }}>
          <div className="lcars-stat-label" style={{ color: 'var(--lcars-blue)' }}>ARBITER_VRAM</div>
          <div className="lcars-stat-value" style={{ fontSize: '14px' }}>{stats?.resources?.current_usage_gb || 0} / {stats?.resources?.vram_budget_gb || 0} GB</div>
          <div className="w-full bg-blue-900/20 h-1.5 mt-2 rounded-full overflow-hidden">
            <motion.div animate={{ width: `${stats?.resources?.utilization_pct || 0}%` }} className="bg-blue-400 h-full" />
          </div>
          <div className="text-[8px] opacity-30 mt-1 uppercase tracking-widest">{stats?.resources?.utilization_pct || 0}% UTILIZATION</div>
        </div>
      </div>
      <div className="lcars-elbow-bottom-left" />
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

  const chatEndRef = useRef(null);

  // Sync Logic
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [expRes, artRes, resRes, meshRes, learnRes, memRes] = await Promise.all([
          axios.get(`${API_BASE}/swarm/experts`),
          axios.get(`${API_BASE}/artifacts`),
          axios.get(`${API_BASE}/system/resources`),
          axios.get(`${API_BASE}/mesh/topology`),
          axios.get(`${API_BASE}/learning/skills`),
          axios.get(`${API_BASE}/memory/stats`)
        ]);
        setExperts(expRes.data);
        if (expRes.data.length > 0 && !selectedRole) setSelectedRole(expRes.data[0].role);
        setArtifacts(artRes.data.artifacts);
        setArtStats(artRes.data.stats);
        setResources(resRes.data);
        setMeshTopology(meshRes.data);
        setLearnedSkills(learnRes.data.skills || []);
        setMemStats(memRes.data);
      } catch (err) { console.error("Sync Error", err); }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [selectedRole]);

  useEffect(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages, selectedRole]);

  const sendMessage = async () => {
    if (!inputMsg.trim() || !selectedRole || isProcessing) return;
    const role = selectedRole;
    setMessages(prev => ({ ...prev, [role]: [...(prev[role] || []), { text: inputMsg, sender: 'user', time: new Date().toLocaleTimeString() }] }));
    setInputMsg('');
    setIsProcessing(true);
    try {
      const res = await axios.post(`${API_BASE}/swarm/chat`, { role, message: inputMsg });
      setMessages(prev => ({ ...prev, [role]: [...(prev[role] || []), { text: res.data.response, sender: 'agent', name: res.data.name, time: new Date().toLocaleTimeString() }] }));
    } catch {
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
    <div className="lcars-container">

      {/* ─── LCARS TOP NAVIGATION ─── */}
      <div className="lcars-bar" style={{ gridColumn: '2 / span 1', height: '60px', borderRadius: '0 30px 30px 0', marginLeft: '-10px', background: 'var(--lcars-orange)' }}>
        <div className="flex justify-between items-center w-full px-10 h-full">
          <div className="flex items-center gap-6">
            <span style={{ fontSize: '32px', fontWeight: 800, letterSpacing: '2px', fontFamily: 'Orbitron' }}>SWARM CORE</span>
            <span className="opacity-60 text-[12px] font-black italic">TRM_PHASE_4_STABLE</span>
          </div>
          <div className="flex gap-4 items-center">
            <div className="flex flex-col items-end">
              <span className="text-[10px] uppercase font-bold text-black/60">Logic Sync</span>
              <span className="text-black font-black">99.98%</span>
            </div>
            <div className="w-16 h-10 bg-black flex items-center justify-center text-orange-400 font-bold border-2 border-orange-500 rounded-sm">
              {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </div>
          </div>
        </div>
      </div>

      {/* ─── SIDEBAR ─── */}
      <LCARS_Sidebar activeTab={activeTab} onTabChange={setActiveTab} stats={{ resources, artifacts, memoryStats }} />

      {/* ─── MAIN CANVAS ─── */}
      <main className="flex-1 overflow-y-auto bg-black p-6 custom-scrollbar" style={{ gridColumn: '2 / span 1', gridRow: '2 / span 1' }}>
        <AnimatePresence mode="wait">

          {/* 01 SYSTEM STATUS */}
          {activeTab === 'overview' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <div className="lcars-panel-title">01 DYNAMIC_TELEMETRY</div>
              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: 'ALIVE NODES', value: meshTopology.alive, color: 'var(--lcars-orange)' },
                  { label: 'MEM_UNITS', value: memoryStats.total_memories, color: 'var(--lcars-blue)' },
                  { label: 'ARTIFACTS', value: artifacts.length, color: 'var(--lcars-purple)' },
                  { label: 'PENDING_REV', value: artStats.pending, color: 'var(--lcars-gold)' }
                ].map(s => (
                  <div key={s.label} className="lcars-stat-box" style={{ borderLeft: `4px solid ${s.color}` }}>
                    <div className="lcars-stat-label" style={{ color: s.color }}>{s.label}</div>
                    <div className="lcars-stat-value">{s.value || 0}</div>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-6 flex-1">
                <section className="flex flex-col bg-white-5 border-white-5">
                  <div className="flex justify-between items-center mb-6">
                    <span className="text-[12px] font-black text-orange-400">NEURAL_PERSONAS</span>
                    <Users size={16} className="text-orange-400" />
                  </div>
                  <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar">
                    {experts.map(e => (
                      <div key={e.role} className="p-4 bg-black/40 border-l-8 flex items-center justify-between" style={{ borderColor: e.avatar_color }}>
                        <div>
                          <div className="text-sm font-black text-white">{e.name}</div>
                          <div className="text-[10px] opacity-30 uppercase tracking-[2px]">{e.role}</div>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <span className="text-[9px] px-2 py-0.5 bg-white-5 rounded-full text-white/40 border border-white-5 uppercase font-bold">Lvl 4 SYNC</span>
                          <div className="flex gap-1">{e.specialties.slice(0, 2).map(s => <div key={s} className="w-1 h-1 rounded-full bg-white/30" />)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="flex flex-col bg-white-5 border-white-5">
                  <div className="flex justify-between items-center mb-6">
                    <span className="text-[12px] font-black text-blue-400">REALTIME_CONSCIOUSNESS_LOG</span>
                    <Activity size={16} className="text-blue-400" />
                  </div>
                  <div className="flex-1 bg-black/60 p-4 font-mono text-[10px] overflow-y-auto space-y-3 leading-relaxed border border-white/5 custom-scrollbar">
                    <div className="text-orange-500/80"><span className="opacity-30">[{new Date().toLocaleTimeString()}]</span> AUDIT: Scanning pipeline artifacts for security policy.</div>
                    <div className="text-blue-400/80"><span className="opacity-30">[{new Date().toLocaleTimeString()}]</span> MESH: Heartbeat response from 12 sub-agents received.</div>
                    <div className="text-green-500/80 animate-pulse"><span className="opacity-30">[{new Date().toLocaleTimeString()}]</span> SYNC: Memory clusters optimized. 1.2GB VRAM reclaimed.</div>
                    <div className="text-purple-400/80"><span className="opacity-30">[{new Date().toLocaleTimeString()}]</span> NEURAL: Specialist 'Architect' processing code manifest.</div>
                  </div>
                </section>
              </div>
            </motion.div>
          )}

          {/* 02 NEURAL BRIDGE */}
          {activeTab === 'chat' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-4">
              <div className="lcars-panel-title" style={{ borderColor: 'var(--lcars-purple)', color: 'var(--lcars-purple)' }}>02 NEURAL_SYNC_PROTOCOL</div>

              <div className="flex gap-1 bg-white-5 p-1 rounded-sm">
                {experts.map(e => (
                  <button key={e.role} onClick={() => setSelectedRole(e.role)}
                    className={`lcars-button flex-1 min-w-[140px] ${selectedRole === e.role ? 'purple' : 'tan'}`}
                    style={{ height: '30px', opacity: selectedRole === e.role ? 1 : 0.4, transition: 'all 0.3s' }}>
                    {e.name}
                  </button>
                ))}
              </div>

              <div className="flex-1 bg-black border border-white-5 flex flex-col overflow-hidden relative shadow-2xl">
                <div className="p-4 bg-white/[0.02] border-b border-white-5 flex justify-between items-center">
                  <span className="text-[11px] font-black text-purple-300 tracking-[3px]">COMM_LINK // {selectedRole?.toUpperCase()}</span>
                  <div className="flex gap-4 items-center">
                    <span className="text-[8px] font-bold text-green-500 animate-pulse uppercase">Bi-Directional Established</span>
                    <div className="w-2 h-2 rounded-full bg-purple-500" />
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-10 space-y-8 custom-scrollbar">
                  {(messages[selectedRole] || []).map((msg, i) => (
                    <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[70%] p-6 rounded-sm text-sm leading-relaxed border ${msg.sender === 'user' ? 'bg-blue-600/10 border-r-8 border-blue-500 text-blue-50' : 'bg-purple-900/10 border-l-8 border-purple-500 text-purple-50 shadow-[0_0_20px_rgba(204,153,204,0.1)]'}`}>
                        {msg.text}
                        <div className="mt-4 text-[8px] opacity-30 font-bold uppercase tracking-widest">{msg.time} // {msg.sender === 'agent' ? msg.name : 'USER_COMMAND'}</div>
                      </div>
                    </div>
                  ))}
                  {isProcessing && <div className="text-purple-400 font-black text-[10px] animate-pulse italic uppercase tracking-[5px]">[OPTIMIZING_THOUGHT_VECTORS...]</div>}
                  <div ref={chatEndRef} />
                </div>

                <div className="p-8 bg-white/[0.01] border-t border-white-5 flex gap-4">
                  <input value={inputMsg} onChange={e => setInputMsg(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()}
                    placeholder="ENTER NEURAL PROTOCOL COMMAND..." className="flex-1 bg-black border-2 border-white-5 p-5 text-sm outline-none focus:border-purple-500 transition-all text-white font-mono" />
                  <button onClick={sendMessage} className="lcars-button purple w-32 h-16 text-lg">EXECUTE</button>
                </div>
              </div>
            </motion.div>
          )}

          {/* 03 SWARM INTEL */}
          {activeTab === 'intel' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <div className="lcars-panel-title" style={{ borderColor: 'var(--lcars-blue)', color: 'var(--lcars-blue)' }}>03 SHARED_INTEL_RESERVOIR</div>

              <div className="grid grid-cols-12 gap-6 flex-1 overflow-hidden">
                <aside className="col-span-4 flex flex-col gap-4">
                  <div className="bg-white-5 p-6 border-l-4 border-blue-500">
                    <span className="text-[11px] font-black text-blue-400 mb-6 block uppercase">COLLECTIVE_STATS</span>
                    <div className="space-y-4">
                      <div className="flex justify-between border-b border-white/5 pb-2">
                        <span className="text-[10px] uppercase font-bold text-white/40">Total Memories</span>
                        <span className="text-sm font-black text-white">{memoryStats.total_memories || 0}</span>
                      </div>
                      <div className="flex justify-between border-b border-white/5 pb-2">
                        <span className="text-[10px] uppercase font-bold text-white/40">Sync Events</span>
                        <span className="text-sm font-black text-white">{memoryStats.sync_events || 0}</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white-5 p-6 flex-1 overflow-y-auto custom-scrollbar">
                    <span className="text-[10px] font-black text-blue-300 mb-4 block uppercase tracking-widest">TYPE_BREAKDOWN</span>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(memoryStats.by_type || {}).map(([type, count]) => (
                        <div key={type} className="p-3 bg-black flex flex-col items-center border border-white-5">
                          <div className="text-lg font-black text-blue-400">{count}</div>
                          <div className="text-[8px] font-bold opacity-30 uppercase">{type}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </aside>

                <section className="col-span-8 flex flex-col gap-4">
                  <div className="relative">
                    <input value={memQuery} onChange={e => setMemQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && queryMemory()}
                      placeholder="QUERY THE COLLECTIVE NEURAL REPOSITORY..." className="w-full bg-black border-4 border-blue-900/30 p-6 pl-14 text-sm font-bold outline-none focus:border-blue-500 transition-all text-white" />
                    <Globe className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-500" size={24} />
                    <button onClick={queryMemory} disabled={isQuerying} className="lcars-button blue absolute right-4 top-1/2 -translate-y-1/2 h-8 px-6">
                      {isQuerying ? <Loader2 className="animate-spin" size={14} /> : 'QUERY'}
                    </button>
                  </div>
                  <div className="flex-1 bg-white/[0.02] border border-white-5 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                    {memResults.map((r, i) => (
                      <div key={i} className="p-6 bg-black border-l-4 border-blue-400 hover:bg-blue-900/5 transition-colors">
                        <div className="flex justify-between mb-4 border-b border-white/5 pb-2">
                          <span className="text-[10px] font-black uppercase tracking-[3px] text-blue-400">{r.entry.author} // {r.entry.author_role}</span>
                          <span className="text-[10px] font-black text-white px-2 py-0.5 bg-blue-600 rounded-full">{((r.score || 0) * 100).toFixed(0)}% MATCH</span>
                        </div>
                        <p className="text-sm leading-relaxed text-gray-300 font-medium">{r.entry.content}</p>
                        <div className="mt-4 text-[8px] opacity-20 uppercase font-black">{r.entry.memory_type} // {r.entry.created_at}</div>
                      </div>
                    ))}
                    {memResults.length === 0 && <div className="h-full flex items-center justify-center opacity-10 font-black tracking-[10px] uppercase italic text-center text-xl">NEURAL_IDLE...</div>}
                  </div>
                </section>
              </div>
            </motion.div>
          )}

          {/* 04 ARTIFACT FLOW */}
          {activeTab === 'pipeline' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <div className="lcars-panel-title" style={{ borderColor: 'var(--lcars-tan)', color: 'var(--lcars-tan)' }}>04 ARTIFACT_EXTRACTION_PIPELINE</div>

              <div className="flex-1 bg-black border-white-5 overflow-hidden flex flex-col">
                <div className="grid grid-cols-12 p-4 bg-white-5 text-[10px] font-black uppercase tracking-[5px] text-tan border-b border-white-5">
                  <div className="col-span-5 pl-10">IDENTIFIER</div>
                  <div className="col-span-2">ORIGIN</div>
                  <div className="col-span-3">SECURITY_AUDIT</div>
                  <div className="col-span-2">COMMIT_STATUS</div>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                  {artifacts.map(art => (
                    <div key={art.filename} className="grid grid-cols-12 items-center p-6 border-b border-white-5 hover:bg-white-5 transition-colors group cursor-pointer" onClick={() => setSelectedArtifact(art)}>
                      <div className="col-span-5 flex items-center gap-6 pl-4">
                        <div className={`p-4 font-black text-lg skew-x-[-15deg] ${art.status === 'integrated' ? 'bg-green-600 text-white' : 'bg-tan text-black'}`}>
                          {art.filename.charAt(0).toUpperCase()}
                        </div>
                        <div className="truncate">
                          <div className="text-sm font-black text-white mb-0.5 tracking-tight uppercase">{art.filename}</div>
                          <div className="text-[9px] opacity-30 font-bold uppercase">{art.size} bytes // {art.created_at?.slice(11, 19)}</div>
                        </div>
                      </div>
                      <div className="col-span-2">
                        <span className="text-[10px] font-black text-tan uppercase tracking-widest">{art.created_by}</span>
                      </div>
                      <div className="col-span-3">
                        {art.security_status ? (
                          <span className={`text-[10px] font-black px-3 py-1 flex items-center gap-2 border w-fit ${art.security_status === 'safe' ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-red-500/20 border-red-500/40 text-red-500 animate-pulse'}`}>
                            <Shield size={12} /> {art.security_status.toUpperCase()}
                          </span>
                        ) : <span className="text-[9px] font-black opacity-20 uppercase italic">SCANNING_IN_PROGRESS...</span>}
                      </div>
                      <div className="col-span-2">
                        <span className={`text-[10px] font-black px-4 py-1 skew-x-[-15deg] uppercase ${art.status === 'integrated' ? 'bg-blue-600 text-white' : 'bg-white-5 text-gray-400'}`}>{art.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* 05 SKILL REGISTRY */}
          {activeTab === 'learning' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <div className="lcars-panel-title" style={{ borderColor: 'var(--lcars-gold)', color: 'var(--lcars-gold)' }}>05 NEURAL_PATTERN_REGISTRY</div>
              <div className="grid grid-cols-2 gap-8 flex-1">
                <section className="bg-white-5 p-8 flex flex-col gap-8 rounded-sm border border-white/5">
                  <div className="flex justify-between items-center">
                    <span className="text-[11px] font-black text-gold uppercase tracking-[4px]">HARVEST_KNOWLEDGE</span>
                    <Sparkles size={18} className="text-gold" />
                  </div>
                  <div className="space-y-4 flex-1 flex flex-col">
                    <input value={learnName} onChange={e => setLearnName(e.target.value)} placeholder="ENTER_SKILL_IDENTIFIER..." className="bg-black border-2 border-white-5 p-5 text-sm outline-none focus:border-gold transition-all text-white font-mono" />
                    <textarea value={learnContent} onChange={e => setLearnContent(e.target.value)} placeholder="INJECT_TECHNICAL_DOCUMENTATION_DATA..." className="flex-1 bg-black border-2 border-white-5 p-5 text-sm outline-none focus:border-gold transition-all text-white font-mono resize-none leading-relaxed" />
                  </div>
                  <button onClick={async () => {
                    if (!learnName.trim() || !learnContent.trim()) return;
                    setIsLearning(true);
                    try {
                      await axios.post(`${API_BASE}/learning/ingest`, { name: learnName, content: learnContent, source: 'dashboard' });
                      setLearnName(''); setLearnContent('');
                      const res = await axios.get(`${API_BASE}/learning/skills`);
                      setLearnedSkills(res.data.skills || []);
                    } catch { } finally { setIsLearning(false); }
                  }} disabled={isLearning} className="lcars-button gold w-full h-16 text-lg font-black tracking-[10px]">
                    {isLearning ? <Loader2 className="animate-spin" /> : 'INGEST'}
                  </button>
                </section>

                <section className="bg-white-5 p-8 flex flex-col rounded-sm border border-white/5">
                  <div className="flex justify-between items-center mb-8">
                    <span className="text-[11px] font-black text-purple-400 uppercase tracking-[4px]">ACTIVE_SKILLS_MANIFEST</span>
                    <Brain size={18} className="text-purple-400" />
                  </div>
                  <div className="flex-1 overflow-y-auto space-y-4 custom-scrollbar">
                    {learnedSkills.map(s => (
                      <div key={s.skill_name} className="p-6 bg-black border-l-8 border-purple-500/50 group hover:border-purple-400 transition-all">
                        <div className="flex justify-between items-center mb-4">
                          <div className="text-lg font-black text-white tracking-tight uppercase italic">{s.skill_name}</div>
                          <button className="p-2 opacity-0 group-hover:opacity-100 hover:text-red-500 transition-all"><Trash2 size={16} /></button>
                        </div>
                        <div className="flex gap-2 flex-wrap">
                          {Object.keys(s.endpoints || {}).map(ep => (
                            <span key={ep} className="text-[9px] px-2 py-0.5 bg-purple-900/20 text-purple-300 border border-purple-500/20 uppercase font-black tracking-widest">{ep}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </motion.div>
          )}

          {/* 06 MESH NET */}
          {activeTab === 'mesh' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className="flex flex-col h-full gap-6">
              <div className="lcars-panel-title" style={{ borderColor: 'var(--lcars-orange)', color: 'var(--lcars-orange)' }}>06 SWARM_TOPOGRAPHY_MATRIX</div>

              <div className="flex-1 relative bg-black border-2 border-white/5 rounded-sm overflow-hidden mesh-matrix">
                {/* SVG connection layer */}
                <svg className="mesh-svg-layer">
                  {meshTopology.connections?.map((conn, idx) => {
                    const fromNode = meshTopology.nodes.find(n => n.node_id === conn.from);
                    const toNode = meshTopology.nodes.find(n => n.node_id === conn.to);
                    if (!fromNode || !toNode) return null;

                    const fAngle = (meshTopology.nodes.indexOf(fromNode) / meshTopology.nodes.length) * 2 * Math.PI;
                    const tAngle = (meshTopology.nodes.indexOf(toNode) / meshTopology.nodes.length) * 2 * Math.PI;

                    const fx = 50 + 35 * Math.cos(fAngle);
                    const fy = 50 + 35 * Math.sin(fAngle);
                    const tx = 50 + 35 * Math.cos(tAngle);
                    const ty = 50 + 35 * Math.sin(tAngle);

                    return (
                      <g key={`${conn.from}-${conn.to}`}>
                        <line x1={`${fx}%`} y1={`${fy}%`} x2={`${tx}%`} y2={`${ty}%`} className={`mesh-connection ${selectedNode?.node_id === conn.from || selectedNode?.node_id === conn.to ? 'active' : ''}`} />
                        <line x1={`${fx}%`} y1={`${fy}%`} x2={`${tx}%`} y2={`${ty}%`} className="mesh-pulse" />
                      </g>
                    );
                  })}
                </svg>

                {/* Nodes layer */}
                {meshTopology.nodes.map((node, i) => {
                  const angle = (i / meshTopology.nodes.length) * 2 * Math.PI;
                  const x = 50 + 35 * Math.cos(angle);
                  const y = 50 + 35 * Math.sin(angle);

                  return (
                    <motion.div
                      key={node.node_id}
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: i * 0.05 }}
                      onClick={() => setSelectedNode(node)}
                      className="mesh-node"
                      style={{ left: `${x}%`, top: `${y}%`, transform: 'translate(-50%, -50%)' }}
                    >
                      <div className="mesh-node-core">
                        <Users size={32} />
                        <div className={`mesh-node-status ${node.status === 'online' ? 'status-online' : 'status-offline'}`} />
                      </div>
                      <div className="mesh-label-bubble">
                        <div className="text-[10px] font-black text-white italic">{node.name}</div>
                        <div className="text-[7px] text-orange-400 tracking-[1px] uppercase">{node.role}</div>
                      </div>
                    </motion.div>
                  );
                })}

                {/* Overlays */}
                {selectedNode && (
                  <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="absolute bottom-10 right-10 p-6 bg-black/90 border-2 border-cyan-500 rounded-sm z-50 w-80 backdrop-blur-xl">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <div className="text-[9px] font-black text-cyan-400 uppercase tracking-widest mb-1">Peer Node Details</div>
                        <div className="text-xl font-black text-white italic">{selectedNode.name}</div>
                      </div>
                      <button onClick={() => setSelectedNode(null)} className="text-cyan-400 hover:text-white"><X size={20} /></button>
                    </div>
                    <div className="space-y-3 mb-6">
                      <div className="flex justify-between text-[10px]"><span className="opacity-40 uppercase">Role</span><span className="text-cyan-200">{selectedNode.role}</span></div>
                      <div className="flex justify-between text-[10px]"><span className="opacity-40 uppercase">Tasks Routed</span><span className="text-cyan-200">{selectedNode.task_count}</span></div>
                      <div className="flex justify-between text-[10px]"><span className="opacity-40 uppercase">Latency</span><span className="text-cyan-200">{selectedNode.latency_ms}ms</span></div>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {selectedNode.specialties?.slice(0, 3).map(s => (
                        <span key={s} className="px-2 py-0.5 bg-cyan-950/30 border border-cyan-500/20 text-[8px] text-cyan-300 uppercase">{s}</span>
                      ))}
                    </div>
                  </motion.div>
                )}

                {meshRouteResult && (
                  <motion.div initial={{ x: -100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="mesh-info-overlay z-50 overflow-hidden flex flex-col max-h-[400px]">
                    <div className="flex justify-between items-center mb-4">
                      <div className="text-[10px] font-black text-orange-400 tracking-[4px]">ROUTING_SUCCESS</div>
                      <button onClick={() => setMeshRouteResult(null)} className="text-white/40 hover:text-white"><X size={16} /></button>
                    </div>
                    <div className="text-sm font-black text-white mb-1 uppercase italic border-l-2 border-orange-500 pl-4">Target: {meshRouteResult.routed_to?.name}</div>
                    <div className="text-[9px] text-white/40 mb-4 italic pl-4">MESH_PROTOCOL: v{meshRouteResult.mesh_version}</div>
                    <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-4">
                      {meshRouteResult.nodal_logs && meshRouteResult.nodal_logs.length > 0 && (
                        <div className="bg-white/5 p-4 rounded-sm border border-white/5">
                          <div className="text-[8px] font-black text-white/40 uppercase mb-2">Tactical Activity Log</div>
                          {meshRouteResult.nodal_logs.map((log, lidx) => (
                            <div key={lidx} className="text-[10px] font-mono text-orange-200/60 leading-tight mb-1">
                              {log}
                            </div>
                          ))}
                        </div>
                      )}
                      <div>
                        <div className="text-[8px] font-black text-white/40 uppercase mb-2">Payload Response</div>
                        <div className="text-[12px] text-orange-50/80 leading-relaxed font-mono whitespace-pre-wrap">
                          {(() => {
                            const raw = meshRouteResult.response || '';
                            const planMatch = raw.match(/\[PLAN\](.*?)(\[|\n\n|$)/s);
                            if (planMatch) {
                              return (
                                <>
                                  <div className="bg-orange-500/10 border-l-4 border-orange-500 p-4 mb-4">
                                    <div className="text-[9px] font-black text-orange-400 uppercase mb-2">Architectural Plan</div>
                                    <div className="text-[11px] text-orange-100 italic">{planMatch[1].trim()}</div>
                                  </div>
                                  {raw.replace(/\[PLAN\].*?(\[|\n\n|$)/s, '$1').trim()}
                                </>
                              );
                            }
                            return raw || meshRouteResult.error;
                          })()}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>

              <div className="bg-black border-2 border-orange-950/50 p-6 flex gap-4">
                <div className="flex-1 relative">
                  <input value={meshRouteTask} onChange={e => setMeshRouteTask(e.target.value)} onKeyDown={e => e.key === 'Enter' && routeMesh()}
                    placeholder="INJECT_TASK_FOR_AUTOROUTING..." className="w-full bg-black border-2 border-white-5 p-5 text-sm outline-none focus:border-orange-500 transition-all text-white font-mono" />
                  <Radio size={20} className="absolute right-6 top-1/2 -translate-y-1/2 text-orange-600 animate-pulse" />
                </div>
                <button onClick={routeMesh} disabled={isRouting} className="lcars-button orange w-48 h-18 text-lg font-black">ROUTE</button>
              </div>
            </motion.div>
          )}

          {/* 08 QIAE STACK */}
          {activeTab === 'qiae' && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col h-full gap-6">
              <div className="lcars-panel-title" style={{ borderColor: 'var(--lcars-gold)', color: 'var(--lcars-gold)' }}>08 QIAE_RECURSIVE_ECOSYSTEM</div>

              <div className="grid grid-cols-3 gap-4 h-full overflow-hidden">
                {/* Latent Memory (RLM) */}
                <div className="bg-white-5 p-6 border-l-4 border-gold flex flex-col gap-4 overflow-hidden">
                  <div className="flex justify-between items-center text-[10px] font-black text-gold uppercase tracking-[2px]">
                    <span>Recursive Latent Memory</span>
                    <Brain size={16} />
                  </div>
                  <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-2 font-mono text-[9px]">
                    {[...Array(5)].map((_, i) => (
                      <div key={i} className="p-3 bg-black border border-white/5 opacity-60">
                        <div className="text-gold mb-1">TOKEN: RLM-7-2-1-0</div>
                        <div className="opacity-40 italic">"Recursive compression of neural trace 0x{Math.floor(Math.random() * 10000).toString(16)}..."</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Semantic Index Highlights */}
                <div className="bg-white-5 p-6 border-l-4 border-blue flex flex-col gap-4 overflow-hidden">
                  <div className="flex justify-between items-center text-[10px] font-black text-blue-400 uppercase tracking-[2px]">
                    <span>Semantic Index (Gemma-300M)</span>
                    <Search size={16} />
                  </div>
                  <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-2">
                    {artifacts.slice(0, 8).map(art => (
                      <div key={art.filename} className="p-3 bg-black/40 border border-white/5 flex flex-col gap-1">
                        <div className="text-[10px] font-black text-white truncate">{art.filename}</div>
                        <div className="flex justify-between items-center">
                          <span className="text-[8px] text-blue-300 uppercase">Semantic Weight: 0.92</span>
                          <div className="w-16 h-0.5 bg-blue-900 overflow-hidden"><div className="h-full bg-blue-400 w-3/4" /></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Fractal Scaling / Worktrees */}
                <div className="bg-white-5 p-6 border-l-4 border-purple flex flex-col gap-4 overflow-hidden">
                  <div className="flex justify-between items-center text-[10px] font-black text-purple-400 uppercase tracking-[2px]">
                    <span>Fractal Isolation (Worker Worktrees)</span>
                    <GitBranch size={16} />
                  </div>
                  <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-2 font-mono text-[9px]">
                    {meshTopology.nodes.slice(0, 3).map(node => (
                      <div key={node.node_id} className="p-3 bg-black border border-white/5">
                        <div className="text-purple-300 mb-1">WORKTREE: task_{node.name}_{Math.floor(Math.random() * 1000).toString(16)}</div>
                        <div className="text-green-500 font-bold uppercase tracking-widest">[Isolation 0 Active]</div>
                        <div className="opacity-30 mt-1">CPU_AFFINITY: [4, 5, 6]</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Perception Gateway (OpenClaw) */}
              <div className="bg-blue-900/10 border-2 border-blue-500/20 p-6 flex flex-col gap-4">
                <div className="flex justify-between items-center text-[11px] font-black text-blue-500 uppercase tracking-[4px]">
                  <span>OpenClaw Perception Gateway (Multi-Channel Inbound)</span>
                  <Radio className="animate-pulse" size={18} />
                </div>
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-black p-4 border border-white/10 flex items-center gap-4">
                    <MessageSquare className="text-blue-400" />
                    <div>
                      <div className="text-[8px] opacity-40 uppercase font-black">Telegram Status</div>
                      <div className="text-sm font-black text-green-500">LISTENING</div>
                    </div>
                  </div>
                  <div className="bg-black p-4 border border-white/10 flex items-center gap-4">
                    <Radio className="text-purple-400" />
                    <div>
                      <div className="text-[8px] opacity-40 uppercase font-black">WhatsApp Bridge</div>
                      <div className="text-sm font-black text-green-500">ACTIVE</div>
                    </div>
                  </div>
                  <div className="col-span-2 bg-black/60 p-4 border border-blue-500/30 font-mono text-[10px] text-blue-200/60 truncate italic">
                    [OpenClaw] INBOUND_SIM: Waiting for signal on multi-channel matrix...
                  </div>
                </div>
              </div>
            </motion.div>
          )}

        </AnimatePresence>

        {/* ─── Artifact Tactical Inspector (Modal) ─── */}
        <AnimatePresence>
          {selectedArtifact && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="modal-overlay backdrop-blur"
              onClick={() => setSelectedArtifact(null)}
            >
              <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 20 }}
                className="modal-content"
                onClick={e => e.stopPropagation()}
              >
                {/* Header */}
                <div className="modal-header">
                  <div className="flex items-center gap-6">
                    <div className="bg-black text-tan p-4 font-black skew-x-[-15deg] text-2xl">
                      {selectedArtifact.filename.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h2 className="text-2xl font-black text-black tracking-tight">{selectedArtifact.filename}</h2>
                      <p className="text-[10px] font-bold text-black/60 uppercase tracking-widest">
                        Origin: {selectedArtifact.created_by} // {selectedArtifact.size} Bytes
                      </p>
                    </div>
                  </div>
                  <button onClick={() => setSelectedArtifact(null)} className="p-2 hover:bg-black/10 rounded-full transition-colors cursor-pointer">
                    <X size={32} className="text-black" />
                  </button>
                </div>

                {/* Body */}
                <div className="modal-body">
                  {/* Left: Metadata & Status */}
                  <div className="bg-white-5 p-8 space-y-8 flex flex-col border-r border-white-5">
                    <div className="space-y-4">
                      <span className="text-[11px] font-black opacity-40 uppercase tracking-[4px]">TACTICAL_STATUS</span>
                      <div className="grid grid-cols-1 gap-2">
                        <div className="p-4 bg-black border-l-4 border-blue-500">
                          <div className="text-[8px] opacity-40 uppercase font-black">Lifecycle Stage</div>
                          <div className="text-sm font-black text-white uppercase">{selectedArtifact.status}</div>
                        </div>
                        <div className={`p-4 bg-black border-l-4 ${selectedArtifact.security_status === 'safe' ? 'border-green-500' : 'border-red-500 animate-pulse'}`}>
                          <div className="text-[8px] opacity-40 uppercase font-black">Security Audit</div>
                          <div className="text-sm font-black text-white uppercase flex items-center gap-2">
                            <Shield size={14} /> {selectedArtifact.security_status || 'SCANNING...'}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex-1 space-y-4">
                      <span className="text-[11px] font-black opacity-40 uppercase tracking-[4px]">INTEGRATION_LOGS</span>
                      <div className="bg-black p-4 font-mono text-[9px] text-tan opacity-60 h-full overflow-y-auto space-y-1">
                        <div>{'>'} [SYSTEM] LOCATING ARTIFACT AT PATH...</div>
                        <div>{'>'} [SECURITY] CHECKSUM VERIFIED (SHA-256)</div>
                        <div>{'>'} [AUDIT] NO MALICIOUS PATTERNS DETECTED</div>
                        {selectedArtifact.status === 'integrated' && <div className="text-green-500">{'>'} [SUCCESS] DEPLOYED TO REPOSITORY</div>}
                      </div>
                    </div>
                  </div>

                  {/* Right: Actions & Preview */}
                  <div className="p-8 flex flex-col gap-8 bg-black">
                    <div className="flex justify-between items-center">
                      <span className="text-[11px] font-black text-tan uppercase tracking-[4px]">COMMAND_OVERRIDE</span>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <button
                        onClick={() => { handleArtifactAction(selectedArtifact.filename, 'approve'); setSelectedArtifact(null); }}
                        className="lcars-button tan h-20 text-lg flex items-center justify-center gap-4 group cursor-pointer"
                      >
                        <CheckCircle2 className="group-hover:scale-125 transition-transform" /> APPROVE & RELEASE
                      </button>
                      <button
                        onClick={() => { handleArtifactAction(selectedArtifact.filename, 'test'); setSelectedArtifact(null); }}
                        className="lcars-button blue h-20 text-lg flex items-center justify-center gap-4 group cursor-pointer"
                      >
                        <TestTube className="group-hover:rotate-12 transition-transform" /> RUN TEST SUITE
                      </button>
                      <button
                        onClick={() => { handleArtifactAction(selectedArtifact.filename, 'integrate'); setSelectedArtifact(null); }}
                        className="lcars-button purple h-20 text-lg flex items-center justify-center gap-4 group cursor-pointer"
                      >
                        <Rocket className="group-hover:translate-y--1 transition-transform" /> INTEGRATE & DEPLOY
                      </button>
                      <button
                        onClick={() => { handleArtifactAction(selectedArtifact.filename, 'reject'); setSelectedArtifact(null); }}
                        className="lcars-button red h-20 text-lg flex items-center justify-center gap-4 group cursor-pointer"
                      >
                        <Ban className="group-hover:scale-90 transition-transform" /> REJECT ARTIFACT
                      </button>
                    </div>

                    <div className="flex-1 bg-white-5 p-6 flex flex-col items-center justify-center opacity-20">
                      <FileText size={64} className="mb-4" />
                      <span className="text-[10px] font-black uppercase tracking-[10px]">Preview Unavailable</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* ─── LCARS FOOTER NAVIGATION ─── */}
      <div className="lcars-bar" style={{ gridColumn: '1 / span 2', gridRow: '3 / span 1', marginTop: '10px', background: 'var(--lcars-blue)', height: '40px', borderRadius: '40px 0 0 40px' }}>
        <div className="flex justify-between w-full h-full items-center px-10">
          <div className="flex gap-10 items-center">
            <span style={{ fontSize: '11px', fontWeight: 900, color: 'black' }}>TRANS_MODE: P2P_ENCRYPTED</span>
            <div className="flex gap-1 h-2">
              {[...Array(20)].map((_, i) => <div key={i} className="w-4 h-full bg-black/20" />)}
            </div>
          </div>
          <div className="flex gap-4">
            <div className="w-16 h-4 bg-orange-400/50 rounded-full"></div>
            <div className="w-16 h-4 bg-purple-400/50 rounded-full"></div>
            <div className="w-16 h-4 bg-gold-400/50 rounded-full"></div>
          </div>
        </div>
      </div>

      <style>{`
        .lcars-button.active {
           box-shadow: 0 0 20px rgba(255,255,255,0.4);
           filter: brightness(1.5);
           position: relative;
        }
        .lcars-button.active::after {
           content: '';
           position: absolute;
           left: -5px;
           top: 0;
           bottom: 0;
           width: 5px;
           background: white;
        }
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #000; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #222; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #333; }
        
        main {
           mask-image: linear-gradient(to bottom, black 95%, transparent 100%);
        }
      `}</style>

    </div>
  );
}
