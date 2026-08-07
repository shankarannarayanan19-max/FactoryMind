import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  Bell,
  ShieldAlert
} from 'lucide-react';
import type { ScenarioTurnState } from '../types/factorymind';

interface LiveEventFeedProps {
  state: ScenarioTurnState;
}

export const LiveEventFeed: React.FC<LiveEventFeedProps> = ({ state }) => {
  const { events } = state;
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  const filteredEvents = events.filter((evt) => {
    if (severityFilter === 'ALL') return true;
    return evt.severity === severityFilter;
  });

  return (
    <div className="hud-panel rounded-2xl border-cyan-500/30 overflow-hidden p-6 bg-[#070c1a]/95">
      <div className="hud-corner-tl" />
      <div className="hud-corner-tr" />
      <div className="hud-corner-bl" />
      <div className="hud-corner-br" />

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-cyan-400 animate-pulse" />
            <h2 className="font-mono text-xl font-extrabold text-white glow-text-cyan tracking-wider">
              REAL-TIME EVENT TICKER & TELEMETRY STREAM
            </h2>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            §12 EVENT TAXONOMY BROADCAST ENGINE ({events.length} LOGGED EVENTS)
          </p>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center gap-1 rounded-lg bg-slate-900 p-1 border border-slate-800">
          {['ALL', 'INFO', 'WARNING', 'CRITICAL', 'SAFETY_BLOCK'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1 font-mono text-[11px] font-bold rounded transition ${
                severityFilter === sev
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/50'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Event List Stream */}
      <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
        <AnimatePresence>
          {filteredEvents.map((evt) => {
            const isCritical = evt.severity === 'CRITICAL' || evt.severity === 'SAFETY_BLOCK';
            const isWarning = evt.severity === 'WARNING';

            return (
              <motion.div
                key={evt.id}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: 20, opacity: 0 }}
                className={`flex items-center justify-between p-4 rounded-xl hud-panel border transition-all ${
                  isCritical
                    ? 'border-rose-500/50 bg-rose-950/20 glow-box-red'
                    : isWarning
                    ? 'border-amber-500/50 bg-amber-950/20'
                    : 'border-slate-800 bg-slate-950/70 hover:border-cyan-500/40'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    isCritical ? 'bg-rose-500/20 text-rose-400' :
                    isWarning ? 'bg-amber-500/20 text-amber-400' :
                    'bg-cyan-500/20 text-cyan-400'
                  }`}>
                    {isCritical ? <ShieldAlert className="h-5 w-5 animate-pulse" /> : <Activity className="h-5 w-5" />}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-white">{evt.event_type}</span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
                        isCritical ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' :
                        isWarning ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' :
                        'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                      }`}>
                        {evt.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 font-sans mt-0.5">
                      {JSON.stringify(evt.payload)}
                    </p>
                  </div>
                </div>

                <div className="text-right font-mono text-xs text-slate-500">
                  <span>TURN {evt.turn}</span>
                  <span className="block text-[10px] text-slate-600">{evt.timestamp}</span>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
};
