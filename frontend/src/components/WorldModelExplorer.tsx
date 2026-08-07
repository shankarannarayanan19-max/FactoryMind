import React, { useMemo, useState } from 'react';
import {
  Background,
  Controls,
  MarkerType,
  ReactFlow
} from '@xyflow/react';
import type { Edge, Node } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Brain, Search } from 'lucide-react';
import type { ScenarioTurnState } from '../types/factorymind';
import { INITIAL_RELATIONSHIPS } from '../services/factorymindData';

interface WorldModelExplorerProps {
  state: ScenarioTurnState;
  onOpenInspector: (id: string) => void;
}

export const WorldModelExplorer: React.FC<WorldModelExplorerProps> = ({ state, onOpenInspector }) => {
  const { assets, sensors, turn } = state;
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Transform WorldModel entities & relationships into React Flow Nodes and Edges
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // 1. Room Nodes
    const roomPositions: Record<string, { x: number; y: number }> = {
      'ROOM-PACK-01': { x: 100, y: 150 },
      'ROOM-CTRL-01': { x: 600, y: 150 },
      'ROOM-WEST-01': { x: 100, y: 500 },
      'ROOM-EAST-01': { x: 600, y: 500 }
    };

    Object.entries(roomPositions).forEach(([rid, pos]) => {
      nodes.push({
        id: rid,
        position: pos,
        data: { label: `ROOM: ${rid}`, type: 'ROOM' },
        style: {
          background: 'rgba(10, 25, 47, 0.9)',
          color: '#00f0ff',
          border: '2px solid #00f0ff',
          borderRadius: '12px',
          padding: '12px 18px',
          fontWeight: 'bold',
          fontFamily: 'monospace',
          boxShadow: '0 0 20px rgba(0, 240, 255, 0.4)'
        }
      });
    });

    // 2. Asset Nodes
    let assetY = 120;
    Object.values(assets).forEach((asset) => {
      const isCritical = asset.health_state === 'CRITICAL';
      const isWarning = asset.health_state === 'WARNING';

      nodes.push({
        id: asset.id,
        position: { x: 340, y: assetY },
        data: { label: `${asset.id}\n[${asset.health_state}]`, type: 'ASSET' },
        style: {
          background: isCritical ? 'rgba(255, 42, 109, 0.25)' : isWarning ? 'rgba(255, 183, 0, 0.25)' : 'rgba(13, 30, 60, 0.85)',
          color: isCritical ? '#ff2a6d' : isWarning ? '#ffb700' : '#e2e8f0',
          border: `2px solid ${isCritical ? '#ff2a6d' : isWarning ? '#ffb700' : '#00ff88'}`,
          borderRadius: '8px',
          padding: '8px 14px',
          fontFamily: 'monospace',
          fontSize: '11px',
          boxShadow: isCritical ? '0 0 15px rgba(255,42,109,0.5)' : 'none'
        }
      });
      assetY += 90;
    });

    // 3. Sensor Nodes
    let sensorY = 150;
    Object.values(sensors).forEach((sensor) => {
      const isCritical = sensor.status === 'CRITICAL' || sensor.status === 'SENSOR_VALIDATION_REQUIRED';
      nodes.push({
        id: sensor.id,
        position: { x: 900, y: sensorY },
        data: { label: `SENSOR: ${sensor.id}\n${sensor.latest_value ?? 'N/A'} ${sensor.unit}`, type: 'SENSOR' },
        style: {
          background: isCritical ? 'rgba(255, 42, 109, 0.3)' : 'rgba(0, 255, 136, 0.15)',
          color: isCritical ? '#ff2a6d' : '#00ff88',
          border: `2px solid ${isCritical ? '#ff2a6d' : '#00ff88'}`,
          borderRadius: '8px',
          padding: '8px 12px',
          fontFamily: 'monospace',
          fontSize: '11px'
        }
      });
      sensorY += 120;
    });

    // 4. Edges from Relationships
    INITIAL_RELATIONSHIPS.forEach((rel) => {
      const isContradiction = rel.relation === 'CONTRADICTS';
      edges.push({
        id: rel.id,
        source: rel.source,
        target: rel.target,
        label: rel.relation,
        animated: isContradiction,
        style: {
          stroke: isContradiction ? '#ff2a6d' : '#00f0ff',
          strokeWidth: isContradiction ? 3 : 1.5
        },
        labelStyle: {
          fill: isContradiction ? '#ff2a6d' : '#00f0ff',
          fontFamily: 'monospace',
          fontSize: '10px',
          fontWeight: 'bold'
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isContradiction ? '#ff2a6d' : '#00f0ff'
        }
      });
    });

    return { initialNodes: nodes, initialEdges: edges };
  }, [assets, sensors, turn]);

  // Filter nodes based on user filter
  const filteredNodes = useMemo(() => {
    return initialNodes.filter((node) => {
      const matchesSearch = searchQuery === '' || node.id.toLowerCase().includes(searchQuery.toLowerCase());
      if (!matchesSearch) return false;

      if (filterType === 'ALL') return true;
      if (filterType === 'ROOMS' && node.data.type === 'ROOM') return true;
      if (filterType === 'ASSETS' && node.data.type === 'ASSET') return true;
      if (filterType === 'SENSORS' && node.data.type === 'SENSOR') return true;
      return true;
    });
  }, [initialNodes, filterType, searchQuery]);

  return (
    <div className="hud-panel rounded-2xl border-cyan-500/30 overflow-hidden p-6 bg-[#070c1a]/95">
      <div className="hud-corner-tl" />
      <div className="hud-corner-tr" />
      <div className="hud-corner-bl" />
      <div className="hud-corner-br" />

      {/* Explorer Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4 z-10 relative">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-cyan-400 animate-pulse" />
            <h2 className="font-mono text-xl font-extrabold text-white glow-text-cyan tracking-wider">
              KNOWLEDGE GRAPH WORLD MODEL EXPLORER
            </h2>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            INTERACTIVE ENTITY NODES & §10 RECONCILIATION RELATIONSHIP GRAPH
          </p>
        </div>

        {/* Search & Filter bar */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search node ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900/90 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 font-mono text-xs text-cyan-300 focus:outline-none focus:border-cyan-400 w-44"
            />
          </div>

          <div className="flex items-center gap-1 rounded-lg bg-slate-900 p-1 border border-slate-800">
            {['ALL', 'ROOMS', 'ASSETS', 'SENSORS'].map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={`px-2.5 py-1 font-mono text-[11px] font-bold rounded transition ${
                  filterType === t
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/50'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* React Flow Canvas Container */}
      <div className="h-[550px] w-full rounded-xl bg-slate-950/90 border border-slate-800 relative overflow-hidden">
        <ReactFlow
          nodes={filteredNodes}
          edges={initialEdges}
          onNodeClick={(_, node) => onOpenInspector(node.id)}
          fitView
        >
          <Background color="#00f0ff" gap={30} size={1} style={{ opacity: 0.1 }} />
          <Controls className="bg-slate-900 text-cyan-400 border border-slate-800" />
        </ReactFlow>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between text-xs font-mono text-slate-400 pt-2 border-t border-slate-800">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-cyan-400" /> ROOM NODES</span>
          <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-emerald-400" /> ASSETS / SENSORS</span>
          <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full bg-rose-500" /> RULE 4 CONTRADICTIONS</span>
        </div>
        <span>CLICK ANY NODE TO LAUNCH OBJECT INSPECTOR</span>
      </div>
    </div>
  );
};
