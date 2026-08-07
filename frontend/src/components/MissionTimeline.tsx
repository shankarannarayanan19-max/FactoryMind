import React from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  AlertOctagon,
  CheckCircle2,
  Clock
} from 'lucide-react';
import type { ScenarioTurnState } from '../types/factorymind';

interface MissionTimelineProps {
  state: ScenarioTurnState;
}

export const MissionTimeline: React.FC<MissionTimelineProps> = ({ state }) => {
  const { pipeline, turn, action_name, command } = state;

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
            <Activity className="h-5 w-5 text-cyan-400 animate-pulse" />
            <h2 className="font-mono text-xl font-extrabold text-white glow-text-cyan tracking-wider">
              MISSION EXECUTION PIPELINE TIMELINE
            </h2>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            LIVE 8-STEP DECISION LOOP (§23 ARCHITECTURE) — TURN {turn}: {action_name}
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-cyan-300 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          <Clock className="h-4 w-4 text-cyan-400" />
          <span>EXECUTED COMMAND:</span>
          <span className="font-bold text-white bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-400/40">
            {command}
          </span>
        </div>
      </div>

      {/* 8-Step Animated Pipeline Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {pipeline.map((step, idx) => {
          const isBlocked = step.status === 'BLOCKED';
          const isCompleted = step.status === 'COMPLETED';

          return (
            <motion.div
              key={step.name}
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: idx * 0.05 }}
              className={`hud-panel rounded-xl p-4 transition-all duration-300 relative ${
                isBlocked
                  ? 'border-rose-500/60 bg-rose-950/20 glow-box-red'
                  : isCompleted
                  ? 'border-emerald-500/40 bg-slate-900/80 hover:border-cyan-400'
                  : 'border-slate-800 bg-slate-950/60'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] font-extrabold text-cyan-400">
                  STEP 0{idx + 1}
                </span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                  isBlocked
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                }`}>
                  {step.status}
                </span>
              </div>

              <h3 className="font-mono text-sm font-bold text-white mb-1.5 flex items-center gap-1.5">
                {isBlocked ? (
                  <AlertOctagon className="h-4 w-4 text-rose-400 animate-pulse" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                )}
                {step.name}
              </h3>

              <p className="text-xs text-slate-300 font-sans leading-relaxed h-10 overflow-hidden">
                {step.detail}
              </p>

              <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/80 mt-2">
                <span>LATENCY</span>
                <span className="text-cyan-400 font-semibold">{step.duration_ms} ms</span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
