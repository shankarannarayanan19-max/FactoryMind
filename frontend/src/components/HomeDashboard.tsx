import React from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Eye,
  Gauge,
  MapPin,
  Shield,
  ShieldAlert,
  Sparkles,
  Zap
} from 'lucide-react';
import type { ScenarioTurnState } from '../types/factorymind';

interface HomeDashboardProps {
  state: ScenarioTurnState;
  setActiveTab: (tab: string) => void;
  onOpenInspector: (id: string) => void;
}

export const HomeDashboard: React.FC<HomeDashboardProps> = ({ state, setActiveTab, onOpenInspector }) => {
  const { mission, agent, assets, sensors, events } = state;

  const contradictionCount = events.filter(e => e.event_type === 'SENSOR_CONTRADICTION').length;
  const criticalCount = Object.values(assets).filter(a => a.health_state === 'CRITICAL').length;

  return (
    <div className="space-y-6 pb-8">
      {/* Hero Overview Header */}
      <div className="hud-panel rounded-xl p-6 border-cyan-500/30 overflow-hidden relative">
        <div className="hud-corner-tl" />
        <div className="hud-corner-tr" />
        <div className="hud-corner-bl" />
        <div className="hud-corner-br" />

        {/* Ambient background glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          <div className="lg:col-span-8 space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <span className="flex items-center gap-1.5 rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-mono font-bold text-cyan-400 border border-cyan-400/30">
                <Sparkles className="h-3.5 w-3.5 animate-spin" />
                DIGITAL TWIN RECONCILIATION ENGINE
              </span>
              <span className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-mono font-bold border ${
                mission.status === 'COMPLETED'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-400/30'
                  : mission.status === 'CRITICAL_HOLD'
                  ? 'bg-amber-500/10 text-amber-400 border-amber-400/30'
                  : 'bg-cyan-500/10 text-cyan-400 border-cyan-400/30'
              }`}>
                <ShieldAlert className="h-3.5 w-3.5" />
                MISSION: {mission.status}
              </span>
            </div>

            <h1 className="text-3xl font-mono font-black tracking-tight text-white glow-text-cyan uppercase">
              {mission.title}
            </h1>

            <p className="text-sm text-slate-300 font-sans leading-relaxed max-w-3xl">
              FactoryMind maintains a persistent state-of-truth across room navigation, sensor telemetry, and dynamic asset changes. Powered by deterministic reconciliation rules and explicit safety interlock validators.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={() => setActiveTab('map')}
                className="flex items-center gap-2 rounded-lg bg-cyan-500/20 px-4 py-2 font-mono text-xs font-bold text-cyan-300 border border-cyan-400/50 hover:bg-cyan-500/30 transition glow-box-cyan"
              >
                <span>OPEN DIGITAL TWIN MAP</span>
                <ArrowRight className="h-4 w-4" />
              </button>

              <button
                onClick={() => setActiveTab('query')}
                className="flex items-center gap-2 rounded-lg bg-slate-900/90 px-4 py-2 font-mono text-xs font-bold text-slate-300 border border-slate-700 hover:bg-slate-800 transition"
              >
                <Cpu className="h-4 w-4 text-cyan-400" />
                <span>INTERROGATE AI WORLD MODEL</span>
              </button>
            </div>
          </div>

          {/* Quick Metrics Cards */}
          <div className="lg:col-span-4 grid grid-cols-2 gap-3">
            <div className="hud-panel rounded-lg p-3.5 border-slate-700/60 bg-slate-950/70">
              <span className="text-[11px] font-mono text-slate-400 block mb-1">MISSION PROGRESS</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-mono font-bold text-cyan-400">{Math.round(mission.progress * 100)}%</span>
                <span className="text-xs text-slate-500">COMPLETE</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                <div className="bg-cyan-400 h-full transition-all duration-500" style={{ width: `${mission.progress * 100}%` }} />
              </div>
            </div>

            <div className="hud-panel rounded-lg p-3.5 border-slate-700/60 bg-slate-950/70">
              <span className="text-[11px] font-mono text-slate-400 block mb-1">SAFETY SCORE</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-mono font-bold text-emerald-400">{mission.safety_score}%</span>
                <span className="text-xs text-emerald-500/80">VERIFIED</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                <div className="bg-emerald-400 h-full" style={{ width: `${mission.safety_score}%` }} />
              </div>
            </div>

            <div className="hud-panel rounded-lg p-3.5 border-slate-700/60 bg-slate-950/70">
              <span className="text-[11px] font-mono text-slate-400 block mb-1">ACTIVE ANOMALIES</span>
              <div className="flex items-baseline gap-2">
                <span className={`text-2xl font-mono font-bold ${criticalCount > 0 ? 'text-rose-400 glow-text-red' : 'text-emerald-400'}`}>
                  {criticalCount}
                </span>
                <span className="text-xs text-slate-500">ASSETS</span>
              </div>
            </div>

            <div className="hud-panel rounded-lg p-3.5 border-slate-700/60 bg-slate-950/70">
              <span className="text-[11px] font-mono text-slate-400 block mb-1">RULE 4 CONTRADICTIONS</span>
              <div className="flex items-baseline gap-2">
                <span className={`text-2xl font-mono font-bold ${contradictionCount > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
                  {contradictionCount}
                </span>
                <span className="text-xs text-slate-500">PENDING</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Agent Status & Key Assets */}
        <div className="lg:col-span-4 space-y-6">
          {/* Agent Status HUD Card */}
          <div className="hud-panel rounded-xl p-5 border-cyan-500/30">
            <div className="hud-corner-tl" />
            <div className="hud-corner-tr" />

            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <Cpu className="h-5 w-5 text-cyan-400" />
                <h2 className="font-mono text-base font-bold text-white uppercase tracking-wider">AUTONOMOUS AGENT STATUS</h2>
              </div>
              <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] font-mono text-emerald-400 border border-emerald-500/30">
                ACTIVE
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between items-center bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-cyan-400" /> LOCATION
                </span>
                <span className="text-cyan-300 font-bold">{agent.room_name} ({agent.location})</span>
              </div>

              <div className="flex justify-between items-center bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Gauge className="h-4 w-4 text-emerald-400" /> CONFIDENCE SCORE
                </span>
                <span className="text-emerald-400 font-bold">{(agent.confidence * 100).toFixed(1)}%</span>
              </div>

              <div className="flex justify-between items-center bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Activity className="h-4 w-4 text-amber-400" /> OPERATIONAL STATE
                </span>
                <span className="text-amber-400 font-bold">{agent.status}</span>
              </div>

              {agent.active_tool && (
                <div className="flex justify-between items-center bg-cyan-950/40 p-2.5 rounded-lg border border-cyan-500/30">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    <Zap className="h-4 w-4 text-cyan-400" /> CARRIED TOOL
                  </span>
                  <span className="text-cyan-300 font-bold">{agent.active_tool}</span>
                </div>
              )}
            </div>
          </div>

          {/* Quick Inspector Launcher Cards */}
          <div className="hud-panel rounded-xl p-5 border-slate-800">
            <h2 className="font-mono text-sm font-bold text-slate-200 mb-3 tracking-wider uppercase">SCENARIO CRITICAL ASSETS</h2>
            <div className="space-y-2">
              {Object.values(assets).map((asset) => (
                <div
                  key={asset.id}
                  onClick={() => onOpenInspector(asset.id)}
                  className={`group flex items-center justify-between p-3 rounded-lg bg-slate-900/70 border transition cursor-pointer hover:bg-slate-800/80 ${
                    asset.health_state === 'CRITICAL'
                      ? 'border-rose-500/40 hover:border-rose-400'
                      : asset.health_state === 'WARNING'
                      ? 'border-amber-500/40 hover:border-amber-400'
                      : 'border-slate-800 hover:border-cyan-500/40'
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-white group-hover:text-cyan-300 transition">{asset.id}</span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                        asset.health_state === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' :
                        asset.health_state === 'WARNING' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
                        'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                      }`}>
                        {asset.health_state}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-sans mt-0.5">{asset.name}</p>
                  </div>
                  <Eye className="h-4 w-4 text-slate-500 group-hover:text-cyan-400 transition" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Mission Objectives & Sensor Live Telemetry */}
        <div className="lg:col-span-8 space-y-6">
          {/* Mission Objectives Checklist */}
          <div className="hud-panel rounded-xl p-5 border-cyan-500/30">
            <div className="hud-corner-tl" />
            <div className="hud-corner-tr" />

            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-cyan-400" />
                <h2 className="font-mono text-base font-bold text-white uppercase tracking-wider">MISSION COMPLETION CONDITIONS</h2>
              </div>
              <span className="font-mono text-xs text-cyan-400">{mission.met_conditions.length} / {mission.met_conditions.length + mission.missing_conditions.length} MET</span>
            </div>

            <div className="space-y-3">
              {mission.met_conditions.map((cond, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 font-mono text-xs text-emerald-300">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span className="flex-1 font-semibold">{cond.replace(/_/g, ' ').toUpperCase()}</span>
                  <span className="text-[10px] bg-emerald-500/20 px-2 py-0.5 rounded text-emerald-400 border border-emerald-400/30">VERIFIED</span>
                </div>
              ))}

              {mission.missing_conditions.map((cond, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-amber-950/20 border border-amber-500/30 font-mono text-xs text-amber-300">
                  <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 animate-pulse" />
                  <span className="flex-1 font-semibold">{cond.replace(/_/g, ' ').toUpperCase()}</span>
                  <span className="text-[10px] bg-amber-500/20 px-2 py-0.5 rounded text-amber-400 border border-amber-400/30">INFORMATION GAP</span>
                </div>
              ))}
            </div>
          </div>

          {/* Telemetry Sensor Live Cards */}
          <div className="hud-panel rounded-xl p-5 border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-mono text-base font-bold text-white uppercase tracking-wider">REAL-TIME SENSOR TELEMETRY</h2>
              <span className="text-xs font-mono text-slate-400">MONITORED BY SCADA</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.values(sensors).map((sensor) => (
                <div
                  key={sensor.id}
                  onClick={() => onOpenInspector(sensor.id)}
                  className={`p-4 rounded-xl bg-slate-950/80 border transition cursor-pointer hover:scale-[1.02] ${
                    sensor.status === 'CRITICAL'
                      ? 'border-rose-500/50 glow-box-red'
                      : sensor.status === 'WARNING'
                      ? 'border-amber-500/50'
                      : 'border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold text-slate-300">{sensor.id}</span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                      sensor.status === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' :
                      sensor.status === 'WARNING' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                      'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    }`}>
                      {sensor.status}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 mb-3 font-sans">{sensor.name}</p>

                  <div className="flex items-baseline justify-between pt-2 border-t border-slate-800/80">
                    <span className="text-xs font-mono text-slate-500">TARGET: {sensor.monitored_asset}</span>
                    <div className="text-right">
                      <span className={`text-2xl font-mono font-black ${
                        sensor.status === 'CRITICAL' ? 'text-rose-400 glow-text-red' : 'text-cyan-400'
                      }`}>
                        {sensor.latest_value ?? 'N/A'}
                      </span>
                      <span className="text-xs font-mono text-slate-400 ml-1">{sensor.unit}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
