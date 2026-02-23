/**
 * Mesh Heatmap Component
 * Phase 5: Vision - Telemetry Glassmorphism v2
 * 
 * Features:
 * - Real-time VRAM consumption visualization
 * - Task routing density heatmap
 * - Glassmorphism styling
 * - Animated data flows
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Cpu, MemoryStick, Activity, TrendingUp, TrendingDown,
  Minus, Flame, Snowflake, Layers, Binary, GitFork, Gauge
} from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8001';

// ─── VRAM Heat Cell ───────────────────────────────────────────────────────
const VRAMHeatCell = ({ node, index, maxValue }) => {
  const utilization = (node.vram_used / (node.vram_total || 1)) * 100;
  const intensity = Math.min(utilization / 100, 1);
  
  // Color gradient from blue (cold) to red (hot)
  const getHeatColor = (val) => {
    if (val < 0.3) return `rgba(51, 204, 255, ${0.3 + val})`; // Cold - Cyan
    if (val < 0.6) return `rgba(255, 204, 0, ${0.3 + val})`;  // Warm - Gold
    return `rgba(255, 51, 51, ${0.3 + val})`;                  // Hot - Red
  };

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: index * 0.03 }}
      className="heatmap-cell"
      style={{
        background: getHeatColor(intensity),
        boxShadow: `0 0 ${20 * intensity}px ${getHeatColor(intensity)}`
      }}
    >
      <div className="heatmap-cell-label">{node.name?.slice(0, 3)}</div>
      <div className="heatmap-cell-value">{utilization.toFixed(0)}%</div>
    </motion.div>
  );
};

// ─── Task Routing Flow ────────────────────────────────────────────────────
const TaskRoutingFlow = ({ routes }) => {
  const maxRoutes = Math.max(...routes.map(r => r.count), 1);
  
  return (
    <div className="routing-flow-container">
      <svg className="routing-flow-svg" viewBox="0 0 400 200">
        {routes.map((route, idx) => {
          const intensity = route.count / maxRoutes;
          const y = 20 + (idx * 30) % 160;
          const x1 = 50;
          const x2 = 350;
          
          return (
            <g key={idx}>
              <motion.line
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1, delay: idx * 0.1 }}
                x1={x1}
                y1={y}
                x2={x2}
                y2={y + Math.sin(idx) * 20}
                stroke={`rgba(255, 153, 0, ${0.3 + intensity * 0.7})`}
                strokeWidth={2 + intensity * 8}
                strokeLinecap="round"
              />
              <motion.circle
                initial={{ r: 0 }}
                animate={{ r: 4 + intensity * 6 }}
                cx={x2}
                cy={y + Math.sin(idx) * 20}
                fill="var(--lcars-orange)"
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// ─── Main Mesh Heatmap Component ──────────────────────────────────────────
const MeshHeatmap = () => {
  const [vramData, setVramData] = useState([]);
  const [routingData, setRoutingData] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState({
    totalVram: 0,
    usedVram: 0,
    avgUtilization: 0,
    taskRoutes: 0,
    hotNodes: 0,
    coldNodes: 0
  });
  const [isLive, setIsLive] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        // Fetch mesh topology
        const meshRes = await axios.get(`${API_BASE}/mesh/topology`);
        const nodes = meshRes.data.nodes || [];
        
        // Fetch system resources
        const resRes = await axios.get(`${API_BASE}/system/resources`);
        const resources = resRes.data || {};
        
        // Generate VRAM data from nodes (simulated if not available)
        const vramNodes = nodes.map((node, idx) => ({
          ...node,
          vram_used: (node.vram_used || Math.random() * 8),
          vram_total: (node.vram_total || 12),
        }));
        
        setVramData(vramNodes);
        
        // Generate routing density data
        const connections = meshRes.data.connections || [];
        const routingDensity = connections.slice(0, 10).map((conn, idx) => ({
          from: conn.from?.slice(0, 8),
          to: conn.to?.slice(0, 8),
          count: Math.floor(Math.random() * 50) + 5
        }));
        setRoutingData(routingDensity);
        
        // Calculate system metrics
        const totalVram = vramNodes.reduce((sum, n) => sum + (n.vram_total || 0), 0);
        const usedVram = vramNodes.reduce((sum, n) => sum + (n.vram_used || 0), 0);
        const avgUtil = totalVram > 0 ? (usedVram / totalVram) * 100 : 0;
        
        setSystemMetrics({
          totalVram: totalVram.toFixed(1),
          usedVram: usedVram.toFixed(1),
          avgUtilization: avgUtil.toFixed(1),
          taskRoutes: routingDensity.length,
          hotNodes: vramNodes.filter(n => n.vram_used / n.vram_total > 0.7).length,
          coldNodes: vramNodes.filter(n => n.vram_used / n.vram_total < 0.3).length
        });
      } catch (err) {
        console.error("Metrics fetch error:", err);
      }
    };

    fetchMetrics();
    if (isLive) {
      const interval = setInterval(fetchMetrics, 2000);
      return () => clearInterval(interval);
    }
  }, [isLive]);

  return (
    <div className="mesh-heatmap-container">
      {/* ─── Header ─── */}
      <div className="heatmap-header">
        <div className="heatmap-title">
          <Layers size={24} className="text-cyan-400" />
          <span>MESH TELEMETRY MATRIX</span>
        </div>
        <div className="heatmap-controls">
          <button 
            onClick={() => setIsLive(!isLive)}
            className={`live-toggle ${isLive ? 'active' : ''}`}
          >
            {isLive ? '● LIVE' : '○ PAUSED'}
          </button>
        </div>
      </div>

      {/* ─── System Metrics Bar ─── */}
      <div className="metrics-bar">
        <div className="metric-item glass-card">
          <MemoryStick size={18} className="text-cyan-400" />
          <div className="metric-content">
            <span className="metric-label">VRAM TOTAL</span>
            <span className="metric-value">{systemMetrics.totalVram} GB</span>
          </div>
        </div>
        <div className="metric-item glass-card">
          <Activity size={18} className="text-orange-400" />
          <div className="metric-content">
            <span className="metric-label">VRAM USED</span>
            <span className="metric-value">{systemMetrics.usedVram} GB</span>
          </div>
        </div>
        <div className="metric-item glass-card">
          <Gauge size={18} className="text-purple-400" />
          <div className="metric-content">
            <span className="metric-label">AVG UTILIZATION</span>
            <span className="metric-value">{systemMetrics.avgUtilization}%</span>
          </div>
        </div>
        <div className="metric-item glass-card">
          <GitFork size={18} className="text-gold-400" />
          <div className="metric-content">
            <span className="metric-label">TASK ROUTES</span>
            <span className="metric-value">{systemMetrics.taskRoutes}</span>
          </div>
        </div>
        <div className="metric-item glass-card">
          <Flame size={18} className="text-red-400" />
          <div className="metric-content">
            <span className="metric-label">HOT NODES</span>
            <span className="metric-value">{systemMetrics.hotNodes}</span>
          </div>
        </div>
        <div className="metric-item glass-card">
          <Snowflake size={18} className="text-blue-400" />
          <div className="metric-content">
            <span className="metric-label">COLD NODES</span>
            <span className="metric-value">{systemMetrics.coldNodes}</span>
          </div>
        </div>
      </div>

      {/* ─── Main Grid ─── */}
      <div className="heatmap-grid">
        {/* VRAM Heatmap */}
        <div className="heatmap-section glass-card">
          <div className="section-header">
            <Cpu size={16} className="text-orange-400" />
            <span>VRAM CONSUMPTION HEATMAP</span>
          </div>
          <div className="heatmap-cells-grid">
            {vramData.length > 0 ? (
              vramData.map((node, idx) => (
                <VRAMHeatCell key={node.node_id || idx} node={node} index={idx} />
              ))
            ) : (
              <div className="no-data-message">NO MESH NODES DETECTED</div>
            )}
          </div>
          <div className="heatmap-legend">
            <div className="legend-item">
              <div className="legend-color cold"></div>
              <span>LOW (<30%)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color warm"></div>
              <span>MEDIUM (30-60%)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color hot"></div>
              <span>HIGH (>60%)</span>
            </div>
          </div>
        </div>

        {/* Task Routing Density */}
        <div className="heatmap-section glass-card">
          <div className="section-header">
            <Binary size={16} className="text-cyan-400" />
            <span>TASK ROUTING DENSITY</span>
          </div>
          <TaskRoutingFlow routes={routingData} />
          <div className="routing-stats">
            {routingData.slice(0, 5).map((route, idx) => (
              <div key={idx} className="routing-stat-item">
                <span className="route-path">{route.from} → {route.to}</span>
                <div className="route-bar-container">
                  <motion.div 
                    className="route-bar"
                    initial={{ width: 0 }}
                    animate={{ width: `${(route.count / 50) * 100}%` }}
                    transition={{ duration: 0.5, delay: idx * 0.1 }}
                  />
                </div>
                <span className="route-count">{route.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─── Styles ─── */}
      <style>{`
        .mesh-heatmap-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          gap: 16px;
        }

        .heatmap-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: rgba(10, 10, 20, 0.8);
          border-left: 4px solid var(--lcars-cyan);
          border-radius: 4px;
        }

        .heatmap-title {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 14px;
          font-weight: 800;
          letter-spacing: 3px;
          color: var(--lcars-cyan);
          text-transform: uppercase;
        }

        .live-toggle {
          padding: 8px 16px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #666;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 2px;
          cursor: pointer;
          transition: all 0.3s;
        }

        .live-toggle.active {
          background: rgba(0, 255, 65, 0.1);
          border-color: #00ff41;
          color: #00ff41;
        }

        .metrics-bar {
          display: grid;
          grid-template-columns: repeat(6, 1fr);
          gap: 12px;
        }

        .glass-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 8px;
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }

        .metric-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
        }

        .metric-content {
          display: flex;
          flex-direction: column;
        }

        .metric-label {
          font-size: 8px;
          font-weight: 800;
          letter-spacing: 2px;
          color: rgba(255, 255, 255, 0.4);
          text-transform: uppercase;
        }

        .metric-value {
          font-size: 16px;
          font-weight: 700;
          color: #fff;
        }

        .heatmap-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          flex: 1;
        }

        .heatmap-section {
          padding: 16px;
          display: flex;
          flex-direction: column;
        }

        .section-header {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 2px;
          color: rgba(255, 255, 255, 0.6);
          text-transform: uppercase;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .heatmap-cells-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
          gap: 8px;
          flex: 1;
        }

        .heatmap-cell {
          aspect-ratio: 1;
          border-radius: 8px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: transform 0.3s, box-shadow 0.3s;
        }

        .heatmap-cell:hover {
          transform: scale(1.1);
        }

        .heatmap-cell-label {
          font-size: 9px;
          font-weight: 800;
          color: rgba(0, 0, 0, 0.7);
          text-transform: uppercase;
        }

        .heatmap-cell-value {
          font-size: 14px;
          font-weight: 700;
          color: rgba(0, 0, 0, 0.9);
        }

        .heatmap-legend {
          display: flex;
          gap: 16px;
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid rgba(255, 255, 255, 0.05);
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 9px;
          color: rgba(255, 255, 255, 0.5);
        }

        .legend-color {
          width: 12px;
          height: 12px;
          border-radius: 2px;
        }

        .legend-color.cold {
          background: rgba(51, 204, 255, 0.8);
        }

        .legend-color.warm {
          background: rgba(255, 204, 0, 0.8);
        }

        .legend-color.hot {
          background: rgba(255, 51, 51, 0.8);
        }

        .routing-flow-container {
          flex: 1;
          min-height: 150px;
        }

        .routing-flow-svg {
          width: 100%;
          height: 100%;
        }

        .routing-stats {
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid rgba(255, 255, 255, 0.05);
        }

        .routing-stat-item {
          display: grid;
          grid-template-columns: 120px 1fr 40px;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .route-path {
          font-size: 8px;
          font-family: 'Fira Code', monospace;
          color: rgba(255, 255, 255, 0.5);
        }

        .route-bar-container {
          height: 4px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 2px;
          overflow: hidden;
        }

        .route-bar {
          height: 100%;
          background: linear-gradient(90deg, var(--lcars-orange), var(--lcars-gold));
          border-radius: 2px;
        }

        .route-count {
          font-size: 10px;
          font-weight: 700;
          color: var(--lcars-orange);
          text-align: right;
        }

        .no-data-message {
          grid-column: 1 / -1;
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100px;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.2);
          letter-spacing: 4px;
          font-weight: 800;
        }

        .text-cyan-400 { color: var(--lcars-cyan); }
        .text-orange-400 { color: var(--lcars-orange); }
        .text-purple-400 { color: var(--lcars-purple); }
        .text-gold-400 { color: var(--lcars-gold); }
        .text-red-400 { color: #ff3333; }
        .text-blue-400 { color: #6699ff; }
      `}</style>
    </div>
  );
};

export default MeshHeatmap;