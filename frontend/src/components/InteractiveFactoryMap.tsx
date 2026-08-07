import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Bot,
  Cpu,
  Maximize2,
  Minimize2,
  Navigation,
  RotateCcw
} from 'lucide-react';
import type { RoomNode, ScenarioTurnState } from '../types/factorymind';
import { INITIAL_ROOMS } from '../services/factorymindData';

interface InteractiveFactoryMapProps {
  state: ScenarioTurnState;
  onOpenInspector: (id: string) => void;
  highlightedRoomId?: string;
}

export const InteractiveFactoryMap: React.FC<InteractiveFactoryMapProps> = ({
  state,
  onOpenInspector,
  highlightedRoomId
}) => {
  const { agent, assets } = state;
  const [zoomLevel, setZoomLevel] = useState<number>(1.0);
  const [selectedRoomId, setSelectedRoomId] = useState<string>('ROOM-PACK-01');

  const selectedRoom: RoomNode = INITIAL_ROOMS[selectedRoomId] || INITIAL_ROOMS['ROOM-PACK-01'];
  const agentRoom = INITIAL_ROOMS[agent.location] || INITIAL_ROOMS['ROOM-PACK-01'];

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.2, 1.8));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.2, 0.7));
  const handleResetZoom = () => setZoomLevel(1.0);

  return (
    <div className="hud-panel rounded-2xl border-cyan-500/30 overflow-hidden relative p-6 bg-[#070c1a]/95">
      <div className="hud-corner-tl" />
      <div className="hud-corner-tr" />
      <div className="hud-corner-bl" />
      <div className="hud-corner-br" />

      {/* Map Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 relative z-10">
        <div>
          <div className="flex items-center gap-2">
            <Navigation className="h-5 w-5 text-cyan-400 animate-pulse" />
            <h2 className="font-mono text-xl font-extrabold text-white glow-text-cyan tracking-wider">
              DIGITAL TWIN TOP-DOWN FACTORY MAP
            </h2>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            REAL-TIME AGENT TRACKING & SPATIAL NODE CONNECTIONS
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Zoom Controls */}
          <div className="flex items-center rounded-lg bg-slate-900/90 border border-slate-800 p-1 font-mono text-xs text-slate-300">
            <button
              onClick={handleZoomOut}
              className="p-1.5 hover:bg-cyan-500/20 hover:text-cyan-300 transition rounded"
              title="Zoom Out"
            >
              <Minimize2 className="h-4 w-4" />
            </button>
            <span className="px-2.5 font-bold text-cyan-400">{(zoomLevel * 100).toFixed(0)}%</span>
            <button
              onClick={handleZoomIn}
              className="p-1.5 hover:bg-cyan-500/20 hover:text-cyan-300 transition rounded"
              title="Zoom In"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1.5 hover:bg-cyan-500/20 hover:text-cyan-300 transition rounded border-l border-slate-800"
              title="Reset View"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          </div>

          <span className="flex items-center gap-1.5 rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-mono text-cyan-400 border border-cyan-400/30">
            <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
            LIVE TELEMETRY REPLAY
          </span>
        </div>
      </div>

      {/* Main Map Viewport & Inspector Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 relative">
        {/* SVG Interactive Canvas */}
        <div className="lg:col-span-8 relative h-[520px] rounded-xl bg-slate-950/90 border border-slate-800/80 overflow-hidden flex items-center justify-center p-4">
          <div
            className="w-full h-full relative transition-transform duration-300 ease-out"
            style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }}
          >
            {/* SVG Lines Connecting Rooms */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
              <defs>
                <linearGradient id="laserGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#00ff88" stopOpacity="0.8" />
                </linearGradient>
              </defs>

              {/* Corridor Lines */}
              <line x1="180" y1="160" x2="520" y2="160" stroke="#00f0ff" strokeWidth="2" strokeDasharray="6 4" className="animate-laser" />
              <line x1="180" y1="160" x2="180" y2="420" stroke="#00f0ff" strokeWidth="2" strokeDasharray="6 4" className="animate-laser" />
              <line x1="520" y1="160" x2="520" y2="420" stroke="#00f0ff" strokeWidth="2" strokeDasharray="6 4" className="animate-laser" />
              <line x1="180" y1="420" x2="520" y2="420" stroke="#00f0ff" strokeWidth="2" strokeDasharray="6 4" className="animate-laser" />
            </svg>

            {/* Room Nodes */}
            {Object.values(INITIAL_ROOMS).map((room) => {
              const isSelected = selectedRoomId === room.id;
              const isHighlighted = highlightedRoomId === room.id;

              return (
                <div
                  key={room.id}
                  onClick={() => setSelectedRoomId(room.id)}
                  style={{ left: room.x - 70, top: room.y - 50 }}
                  className={`absolute w-36 h-28 rounded-xl p-3 cursor-pointer transition-all duration-300 z-10 hud-panel ${
                    isSelected
                      ? 'border-cyan-400 bg-cyan-950/40 glow-box-cyan scale-105'
                      : isHighlighted
                      ? 'border-amber-400 bg-amber-950/30 scale-105 animate-pulse'
                      : 'border-slate-800 hover:border-cyan-500/50 bg-slate-900/80 hover:scale-102'
                  }`}
                >
                  <div className="hud-corner-tl" />
                  <div className="hud-corner-tr" />

                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-[11px] font-extrabold text-cyan-400">{room.code}</span>
                    <span className={`h-2 w-2 rounded-full ${
                      room.status === 'CRITICAL' ? 'bg-rose-400 animate-ping' :
                      room.status === 'WARNING' ? 'bg-amber-400 animate-pulse' :
                      'bg-emerald-400'
                    }`} />
                  </div>

                  <h3 className="font-mono text-xs font-bold text-white truncate">{room.name}</h3>
                  <p className="text-[10px] text-slate-400 font-mono mt-1">{room.assets.length} ASSETS</p>

                  <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-slate-500 border-t border-slate-800/80 pt-1">
                    <span>STATUS</span>
                    <span className={room.status === 'CRITICAL' ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                      {room.status}
                    </span>
                  </div>
                </div>
              );
            })}

            {/* Animated Agent Marker */}
            <motion.div
              animate={{
                x: agentRoom.x - 20,
                y: agentRoom.y - 20
              }}
              transition={{ duration: 1.2, ease: 'easeInOut' }}
              className="absolute z-20 pointer-events-none"
            >
              <div className="relative flex items-center justify-center h-10 w-10">
                <div className="absolute inset-0 rounded-full bg-cyan-400/40 animate-ping" />
                <div className="relative flex h-9 w-9 items-center justify-center rounded-full bg-cyan-950 border-2 border-cyan-400 shadow-[0_0_20px_#00f0ff]">
                  <Bot className="h-5 w-5 text-cyan-300 animate-pulse" />
                </div>
                <div className="absolute -bottom-5 font-mono text-[9px] font-extrabold text-cyan-300 bg-slate-950/90 px-1.5 py-0.5 rounded border border-cyan-400/40 whitespace-nowrap shadow-lg">
                  AGENT-01
                </div>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Selected Room Inspector Panel */}
        <div className="lg:col-span-4 hud-panel rounded-xl p-5 border-slate-800 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="font-mono text-xs text-cyan-400 font-bold">{selectedRoom.code}</span>
                <h3 className="font-mono text-lg font-bold text-white">{selectedRoom.name}</h3>
              </div>
              <span className={`text-xs font-mono px-2 py-0.5 rounded font-bold border ${
                selectedRoom.status === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border-rose-500/40' :
                'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
              }`}>
                {selectedRoom.status}
              </span>
            </div>

            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              {selectedRoom.description}
            </p>

            {/* Room Assets List */}
            <div className="space-y-2">
              <span className="font-mono text-xs font-bold text-slate-400 tracking-wider block">
                LOCATED ASSETS ({selectedRoom.assets.length})
              </span>
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {selectedRoom.assets.map((assetId) => {
                  const asset = assets[assetId];
                  return (
                    <div
                      key={assetId}
                      onClick={() => onOpenInspector(assetId)}
                      className="flex items-center justify-between p-2.5 rounded bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition"
                    >
                      <div className="flex items-center gap-2">
                        <Cpu className="h-3.5 w-3.5 text-cyan-400" />
                        <span className="font-mono text-xs font-bold text-slate-200">{assetId}</span>
                      </div>
                      <span className={`text-[10px] font-mono font-semibold ${
                        asset?.health_state === 'CRITICAL' ? 'text-rose-400' : 'text-emerald-400'
                      }`}>
                        {asset?.health_state || 'NORMAL'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Connected Exits */}
            <div>
              <span className="font-mono text-xs font-bold text-slate-400 tracking-wider block mb-1.5">
                INTER-ROOM EXITS
              </span>
              <div className="flex flex-wrap gap-2">
                {Object.entries(selectedRoom.exits).map(([dir, roomId]) => (
                  <button
                    key={roomId}
                    onClick={() => setSelectedRoomId(roomId)}
                    className="flex items-center gap-1.5 rounded bg-slate-900 px-2.5 py-1 font-mono text-xs text-cyan-300 border border-slate-700 hover:bg-cyan-950/40 hover:border-cyan-400 transition"
                  >
                    <span className="text-slate-500 capitalize">{dir}:</span>
                    <span className="font-bold">{roomId}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 text-center">
            <span className="font-mono text-[11px] text-slate-500">
              CLICK ANY ROOM NODE TO INSPECT SUB-COMPONENTS
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
