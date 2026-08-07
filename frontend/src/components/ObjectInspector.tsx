import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import type { AssetObject, RoomNode, ScenarioTurnState, SensorObject } from '../types/factorymind';
import { INITIAL_ROOMS } from '../services/factorymindData';

interface ObjectInspectorProps {
  objectId: string | null;
  state: ScenarioTurnState;
  onClose: () => void;
}

export const ObjectInspector: React.FC<ObjectInspectorProps> = ({ objectId, state, onClose }) => {
  if (!objectId) return null;

  const { assets, sensors } = state;

  // Resolve item target
  const asset: AssetObject | undefined = assets[objectId];
  const sensor: SensorObject | undefined = sensors[objectId];
  const room: RoomNode | undefined = INITIAL_ROOMS[objectId];

  const name = asset?.name || sensor?.name || room?.name || objectId;
  const type = asset?.type || sensor?.type || (room ? 'ROOM' : 'UNKNOWN');
  const healthStatus = asset?.health_state || sensor?.status || room?.status || 'NORMAL';
  const confidence = asset?.confidence || 0.99;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="w-full max-w-md h-full hud-panel border-l border-cyan-500/40 bg-[#070d1e]/98 p-6 overflow-y-auto shadow-2xl relative"
        >
          <div className="hud-corner-tl" />
          <div className="hud-corner-bl" />

          {/* Drawer Header */}
          <div className="flex items-start justify-between border-b border-slate-800 pb-4 mb-6">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-cyan-400">{objectId}</span>
                <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[10px] text-slate-300 border border-slate-700">
                  {type}
                </span>
              </div>
              <h2 className="font-mono text-xl font-extrabold text-white mt-1">{name}</h2>
            </div>

            <button
              onClick={onClose}
              className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Status & Confidence Badge Banner */}
          <div className="grid grid-cols-2 gap-3 mb-6 font-mono text-xs">
            <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800">
              <span className="text-slate-400 block mb-1 text-[10px]">HEALTH STATUS</span>
              <span className={`font-extrabold text-sm ${
                healthStatus === 'CRITICAL' || healthStatus === 'SENSOR_VALIDATION_REQUIRED'
                  ? 'text-rose-400 glow-text-red'
                  : healthStatus === 'WARNING'
                  ? 'text-amber-400'
                  : 'text-emerald-400'
              }`}>
                {healthStatus}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800">
              <span className="text-slate-400 block mb-1 text-[10px]">AI CONFIDENCE</span>
              <span className="font-extrabold text-sm text-cyan-400">{(confidence * 100).toFixed(1)}%</span>
            </div>
          </div>

          {/* Sub-component Details Section */}
          <div className="space-y-6 font-mono text-xs">
            {/* Operational States */}
            {asset && (
              <div className="space-y-2 bg-slate-950/70 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 font-bold tracking-wider block mb-2">DYNAMIC STATES (§10 RULE 2)</span>
                <div className="flex justify-between items-center py-1 border-b border-slate-900">
                  <span className="text-slate-400">OPERATIONAL STATE:</span>
                  <span className="text-cyan-300 font-bold">{asset.operational_state}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-slate-900">
                  <span className="text-slate-400">ENERGY STATE:</span>
                  <span className="text-cyan-300 font-bold">{asset.energy_state}</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-400">ACCESS GUARD STATE:</span>
                  <span className="text-cyan-300 font-bold">{asset.access_state}</span>
                </div>
              </div>
            )}

            {/* Sensor Reading Details */}
            {sensor && (
              <div className="space-y-2 bg-cyan-950/30 p-4 rounded-xl border border-cyan-500/30">
                <span className="text-cyan-400 font-bold tracking-wider block mb-2">TELEMETRY READING</span>
                <div className="flex items-baseline justify-between">
                  <span className="text-slate-300">LATEST VALUE:</span>
                  <span className="text-2xl font-bold text-cyan-300 glow-text-cyan">
                    {sensor.latest_value ?? 'N/A'} {sensor.unit}
                  </span>
                </div>
                <div className="flex justify-between items-center text-slate-400 pt-1">
                  <span>MONITORED TARGET:</span>
                  <span className="text-white font-bold">{sensor.monitored_asset}</span>
                </div>
                {sensor.alarm && (
                  <div className="mt-2 p-2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[11px]">
                    ALARM: {sensor.alarm}
                  </div>
                )}
              </div>
            )}

            {/* Entity Relationships */}
            {asset?.relationships && asset.relationships.length > 0 && (
              <div className="space-y-2">
                <span className="text-slate-400 font-bold tracking-wider block">STATIC RELATIONSHIPS (§10 RULE 3)</span>
                <div className="space-y-1.5">
                  {asset.relationships.map((rel, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2.5 rounded bg-slate-900/80 border border-slate-800">
                      <span className="text-cyan-400 font-semibold">{rel.relation.toUpperCase()}</span>
                      <span className="text-slate-200 font-bold">{rel.target}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Property Specs */}
            {asset?.properties && (
              <div className="space-y-2">
                <span className="text-slate-400 font-bold tracking-wider block">TECHNICAL SPECIFICATIONS</span>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1 text-slate-300 font-mono text-[11px]">
                  {Object.entries(asset.properties).map(([k, v]) => (
                    <div key={k} className="flex justify-between py-0.5 border-b border-slate-900">
                      <span className="text-slate-500 capitalize">{k.replace(/_/g, ' ')}:</span>
                      <span className="font-semibold text-slate-200">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* State History Timeline */}
            {asset?.history && asset.history.length > 0 && (
              <div className="space-y-2">
                <span className="text-slate-400 font-bold tracking-wider block">STATE HISTORY TIMELINE</span>
                <div className="space-y-2 pl-2 border-l-2 border-cyan-500/40">
                  {asset.history.map((hist, idx) => (
                    <div key={idx} className="relative pl-3 space-y-0.5">
                      <span className="absolute -left-[11px] top-1.5 h-2 w-2 rounded-full bg-cyan-400" />
                      <div className="flex justify-between text-slate-400 text-[10px]">
                        <span>TURN {hist.turn}</span>
                        <span>{hist.state_key}</span>
                      </div>
                      <p className="text-slate-200 font-semibold text-[11px]">
                        {String(hist.old_value)} → <span className="text-cyan-300">{String(hist.new_value)}</span>
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
