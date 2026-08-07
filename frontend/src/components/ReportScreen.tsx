import React from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import {
  Award,
  Clock,
  Download,
  FileCheck,
  Layers,
  ShieldCheck
} from 'lucide-react';
import type { ScenarioTurnState } from '../types/factorymind';

interface ReportScreenProps {
  state: ScenarioTurnState;
}

export const ReportScreen: React.FC<ReportScreenProps> = ({ state }) => {
  const { mission, telemetry_trends, assets, sensors, events } = state;

  const downloadJson = () => {
    const reportData = {
      report_id: `RPT-${mission.mission_id}-001`,
      mission_id: mission.mission_id,
      mission_status: mission.status,
      score: mission.score,
      safety_score: mission.safety_score,
      evidence: Object.values(sensors).map(s => ({
        sensor_id: s.id,
        monitored_asset: s.monitored_asset,
        value: s.latest_value,
        unit: s.unit,
        status: s.status
      })),
      safety_checks: events.filter(e => e.severity === 'SAFETY_BLOCK' || e.event_type === 'SHUTDOWN_REQUESTED'),
      diagnosis: 'Severe bearing degradation on CV-M02 causing elevated temperature (82.0 C) and RMS vibration (5.8 mm/s)',
      severity: 'CRITICAL',
      recommendation: 'Schedule bearing replacement on CV-M02 before restarting Conveyor Line 1 (CV-01)',
      repair_performed: false
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `FactoryMind_Report_${mission.mission_id}.json`;
    a.click();
  };

  return (
    <div className="space-y-6 pb-10">
      {/* Top Metrics Banner */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="hud-panel rounded-xl p-5 border-cyan-500/40 bg-slate-950/80">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-xs font-bold text-slate-400">MISSION SCORE</span>
            <Award className="h-5 w-5 text-cyan-400 glow-text-cyan" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-3xl font-black text-cyan-400 glow-text-cyan">{mission.score}</span>
            <span className="font-mono text-xs text-slate-500">/ 100</span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className="bg-cyan-400 h-full" style={{ width: `${mission.score}%` }} />
          </div>
        </div>

        <div className="hud-panel rounded-xl p-5 border-emerald-500/40 bg-slate-950/80">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-xs font-bold text-slate-400">SAFETY INTEGRITY</span>
            <ShieldCheck className="h-5 w-5 text-emerald-400 glow-text-green" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-3xl font-black text-emerald-400 glow-text-green">{mission.safety_score}%</span>
            <span className="font-mono text-xs text-emerald-500">VERIFIED</span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className="bg-emerald-400 h-full" style={{ width: `${mission.safety_score}%` }} />
          </div>
        </div>

        <div className="hud-panel rounded-xl p-5 border-amber-500/40 bg-slate-950/80">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-xs font-bold text-slate-400">OBJECTS SCANNED</span>
            <Layers className="h-5 w-5 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-3xl font-black text-amber-400">{Object.keys(assets).length}</span>
            <span className="font-mono text-xs text-slate-500">ASSETS RECONCILED</span>
          </div>
        </div>

        <div className="hud-panel rounded-xl p-5 border-purple-500/40 bg-slate-950/80">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-xs font-bold text-slate-400">EXECUTION LATENCY</span>
            <Clock className="h-5 w-5 text-purple-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-3xl font-black text-purple-400">3.42</span>
            <span className="font-mono text-xs text-slate-500">SECONDS</span>
          </div>
        </div>
      </div>

      {/* Main Level 4 Report Container */}
      <div className="hud-panel rounded-2xl border-cyan-500/30 overflow-hidden p-6 bg-[#070c1a]/95">
        <div className="hud-corner-tl" />
        <div className="hud-corner-tr" />
        <div className="hud-corner-bl" />
        <div className="hud-corner-br" />

        {/* Report Header & Export Actions */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <FileCheck className="h-5 w-5 text-cyan-400 animate-pulse" />
              <h2 className="font-mono text-xl font-extrabold text-white glow-text-cyan tracking-wider">
                LEVEL 4 FINAL STRUCTURED MISSION REPORT (§19 OUTPUT 4)
              </h2>
            </div>
            <p className="text-xs font-mono text-slate-400 mt-1">
              REPORT ID: RPT-{mission.mission_id}-001 • GENERATED VIA FACTORYMIND AGENT ENGINE
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={downloadJson}
              className="flex items-center gap-2 rounded-lg bg-cyan-500/20 px-4 py-2 font-mono text-xs font-bold text-cyan-300 border border-cyan-400/50 hover:bg-cyan-500/30 transition shadow-[0_0_10px_rgba(0,240,255,0.2)]"
            >
              <Download className="h-4 w-4 text-cyan-400" />
              <span>DOWNLOAD JSON REPORT</span>
            </button>
          </div>
        </div>

        {/* Diagnosis & Recommendations Panel */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 font-mono text-xs">
          <div className="hud-panel rounded-xl p-5 border-rose-500/40 bg-rose-950/20">
            <span className="text-rose-400 font-bold tracking-wider block mb-2 text-xs">
              AI DIAGNOSIS & ROOT CAUSE
            </span>
            <p className="text-white font-sans text-sm leading-relaxed font-semibold">
              Severe bearing degradation on CV-M02 causing elevated bearing temperature (82.0 C) and RMS vibration (5.8 mm/s). Contradiction protocol Rule 4 sets status to SENSOR_VALIDATION_REQUIRED.
            </p>
          </div>

          <div className="hud-panel rounded-xl p-5 border-emerald-500/40 bg-emerald-950/20">
            <span className="text-emerald-400 font-bold tracking-wider block mb-2 text-xs">
              MAINTENANCE RECOMMENDATION
            </span>
            <p className="text-white font-sans text-sm leading-relaxed font-semibold">
              Schedule bearing replacement on CV-M02 before restarting Conveyor Line 1 (CV-01). Perform pyrometer calibration on TS-CVM02-BRG.
            </p>
          </div>
        </div>

        {/* Telemetry Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Temperature Trend Line Chart */}
          <div className="hud-panel rounded-xl p-5 border-slate-800 bg-slate-950/90">
            <span className="font-mono text-xs font-bold text-cyan-400 tracking-wider block mb-4">
              TEMPERATURE TELEMETRY TREND (°C)
            </span>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={telemetry_trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" stroke="#64748b" style={{ fontSize: '11px', fontFamily: 'monospace' }} />
                  <YAxis stroke="#64748b" style={{ fontSize: '11px', fontFamily: 'monospace' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#00f0ff', fontSize: '12px', fontFamily: 'monospace' }} />
                  <Line type="monotone" dataKey="temperature" stroke="#00f0ff" strokeWidth={3} dot={{ r: 4, fill: '#00f0ff' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Vibration Trend Bar Chart */}
          <div className="hud-panel rounded-xl p-5 border-slate-800 bg-slate-950/90">
            <span className="font-mono text-xs font-bold text-amber-400 tracking-wider block mb-4">
              VIBRATION RMS TREND (mm/s)
            </span>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={telemetry_trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" stroke="#64748b" style={{ fontSize: '11px', fontFamily: 'monospace' }} />
                  <YAxis stroke="#64748b" style={{ fontSize: '11px', fontFamily: 'monospace' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#ffb700', fontSize: '12px', fontFamily: 'monospace' }} />
                  <Bar dataKey="vibration" fill="#ffb700" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
