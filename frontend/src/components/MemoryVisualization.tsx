import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Database } from 'lucide-react';
import type { ScenarioTurnState } from '../types/factorymind';

interface MemoryVisualizationProps {
  state: ScenarioTurnState;
}

export const MemoryVisualization: React.FC<MemoryVisualizationProps> = ({ state }) => {
  const { memories, events, assets, sensors } = state;
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');

  const filteredMemories = memories.filter((m) => {
    if (selectedFilter === 'ALL') return true;
    return m.type === selectedFilter;
  });

  return (
    <div className="hud-panel rounded-2xl border-cyan-500/30 overflow-hidden p-6 bg-[#070c1a]/95">
      <div className="hud-corner-tl" />
      <div className="hud-corner-tr" />
      <div className="hud-corner-bl" />
      <div className="hud-corner-br" />

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-cyan-400 animate-pulse" />
            <h2 className="font-mono text-xl font-extrabold text-white glow-text-cyan tracking-wider">
              PERSISTENT AI MEMORY BANK & EVENT LEDGER
            </h2>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            STACKED MEMORY CARDS, SNAPSHOTS & §10 RULE 4 CONTRADICTION AUDIT
          </p>
        </div>

        {/* Memory Filter Tabs */}
        <div className="flex items-center gap-1 rounded-lg bg-slate-900 p-1 border border-slate-800">
          {['ALL', 'OBSERVATION', 'FACT', 'RECONCILED_SNAPSHOT', 'CONTRADICTION_RULE4'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedFilter(cat)}
              className={`px-3 py-1 font-mono text-[11px] font-bold rounded transition ${
                selectedFilter === cat
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/50'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {cat.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Memory Cards & Facts Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Stacked Memory Cards */}
        <div className="lg:col-span-7 space-y-4">
          <span className="font-mono text-xs font-bold text-slate-400 tracking-wider block">
            PERSISTED MEMORY CARDS ({filteredMemories.length})
          </span>

          <div className="space-y-4">
            {filteredMemories.map((card, idx) => (
              <motion.div
                key={card.id}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: idx * 0.1 }}
                className={`hud-panel rounded-xl p-5 border transition-all duration-300 relative ${
                  card.type === 'CONTRADICTION_RULE4'
                    ? 'border-amber-500/60 bg-amber-950/20 glow-box-amber'
                    : card.type === 'RECONCILED_SNAPSHOT'
                    ? 'border-emerald-500/40 bg-slate-900/90'
                    : 'border-slate-800 bg-slate-950/80 hover:border-cyan-500/40'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-extrabold text-cyan-400">{card.id}</span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
                      card.type === 'CONTRADICTION_RULE4'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                    }`}>
                      {card.type}
                    </span>
                  </div>
                  <span className="font-mono text-xs text-slate-500">TURN {card.turn}</span>
                </div>

                <h3 className="font-mono text-sm font-bold text-white mb-1.5">{card.title}</h3>
                <p className="text-xs text-slate-300 font-sans leading-relaxed mb-3">
                  {card.summary}
                </p>

                {/* Card Details Payload */}
                <div className="rounded bg-slate-950 p-3 font-mono text-[11px] text-slate-400 border border-slate-800/80 space-y-1">
                  {Object.entries(card.details).map(([k, v]) => (
                    <div key={k} className="flex justify-between py-0.5">
                      <span className="text-slate-500 capitalize">{k.replace(/_/g, ' ')}:</span>
                      <span className="text-cyan-300 font-bold">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Right Column: Reconciled Fact Ledger & Event Audit */}
        <div className="lg:col-span-5 space-y-6">
          {/* Active Facts Snapshot */}
          <div className="hud-panel rounded-xl p-5 border-slate-800 bg-slate-950/90">
            <h3 className="font-mono text-sm font-bold text-white mb-3 tracking-wider uppercase">
              ACTIVE FACT SNAPSHOT (§11 SCHEMA)
            </h3>
            <div className="space-y-2 font-mono text-xs">
              <div className="p-3 rounded bg-slate-900 border border-slate-800 flex justify-between">
                <span className="text-slate-400">AGENT LOCATION:</span>
                <span className="text-cyan-300 font-bold">{state.agent.room_name} ({state.agent.location})</span>
              </div>
              <div className="p-3 rounded bg-slate-900 border border-slate-800 flex justify-between">
                <span className="text-slate-400">TRACKED ASSETS:</span>
                <span className="text-emerald-400 font-bold">{Object.keys(assets).length} RECONCILED</span>
              </div>
              <div className="p-3 rounded bg-slate-900 border border-slate-800 flex justify-between">
                <span className="text-slate-400">ACTIVE TELEMETRY READINGS:</span>
                <span className="text-amber-400 font-bold">{Object.keys(sensors).length} SENSORS</span>
              </div>
            </div>
          </div>

          {/* Bounded Event Log */}
          <div className="hud-panel rounded-xl p-5 border-slate-800 bg-slate-950/90">
            <h3 className="font-mono text-sm font-bold text-white mb-3 tracking-wider uppercase">
              BOUNDED EVENT LOG ({events.length})
            </h3>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {events.map((evt) => (
                <div
                  key={evt.id}
                  className="p-2.5 rounded bg-slate-900/80 border border-slate-800 text-xs font-mono flex items-center justify-between"
                >
                  <div>
                    <span className="text-cyan-400 font-bold block">{evt.event_type}</span>
                    <span className="text-[10px] text-slate-500">TURN {evt.turn} • {evt.timestamp}</span>
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold border ${
                    evt.severity === 'WARNING' || evt.severity === 'SAFETY_BLOCK'
                      ? 'bg-amber-500/20 text-amber-400 border-amber-500/40'
                      : 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40'
                  }`}>
                    {evt.severity}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
