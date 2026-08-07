import React, { useEffect, useState } from 'react';
import {
  Activity,
  Brain,
  Clock,
  Cpu,
  Database,
  LayoutDashboard,
  Map,
  MessageSquare,
  Pause,
  Play,
  StepBack,
  StepForward
} from 'lucide-react';
import { factorymindData } from '../services/factorymindData';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const [timeStr, setTimeStr] = useState<string>('');
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTurn, setCurrentTurn] = useState<number>(1);
  const totalTurns = factorymindData.getTurnCount();

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setTimeStr(
        `SYS.CLK ${now.getUTCFullYear()}.${String(now.getUTCMonth() + 1).padStart(2, '0')}.${String(now.getUTCDate()).padStart(2, '0')} ${String(now.getUTCHours()).padStart(2, '0')}:${String(now.getUTCMinutes()).padStart(2, '0')}:${String(now.getUTCSeconds()).padStart(2, '0')}.${String(now.getUTCMilliseconds()).padStart(3, '0')} Z`
      );
    };

    updateClock();
    const interval = setInterval(updateClock, 80);

    const unsubscribe = factorymindData.subscribe(() => {
      setIsPlaying(factorymindData.isPlaying());
      setCurrentTurn(factorymindData.getCurrentState().turn);
    });

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, []);

  const navItems = [
    { id: 'dashboard', label: 'OVERVIEW', icon: LayoutDashboard },
    { id: 'map', label: 'DIGITAL TWIN MAP', icon: Map },
    { id: 'graph', label: 'WORLD MODEL', icon: Brain },
    { id: 'memory', label: 'MEMORY BANK', icon: Database },
    { id: 'query', label: 'AI JARVIS QUERY', icon: MessageSquare },
    { id: 'report', label: 'REPORTS & ANALYTICS', icon: Activity }
  ];

  return (
    <header className="relative z-30 w-full hud-panel border-b border-cyan-500/30 bg-[#070b16]/90 backdrop-blur-xl px-4 py-2.5 shadow-2xl">
      <div className="hud-corner-tl" />
      <div className="hud-corner-tr" />

      <div className="mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Logo & Agent HUD Badge */}
        <div className="flex items-center gap-4">
          <div className="relative flex items-center gap-3 group cursor-pointer" onClick={() => setActiveTab('dashboard')}>
            <div className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-950/80 border border-cyan-400/50 shadow-[0_0_15px_rgba(0,240,255,0.4)]">
              <Cpu className="h-6 w-6 text-cyan-400 animate-pulse" />
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
              </span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-lg font-extrabold tracking-wider text-cyan-400 glow-text-cyan">
                  FACTORY<span className="text-white">MIND</span>
                </span>
                <span className="rounded bg-cyan-500/20 px-1.5 py-0.5 text-[10px] font-mono font-bold tracking-widest text-cyan-300 border border-cyan-400/30">
                  AI WORLD MODEL v2.4
                </span>
              </div>
              <p className="text-[11px] font-mono text-slate-400">AUTONOMOUS DIGITAL TWIN PLATFORM</p>
            </div>
          </div>

          <div className="hidden lg:flex items-center gap-3 border-l border-slate-800 pl-4">
            <div className="flex items-center gap-2 rounded-full bg-slate-900/80 px-3 py-1 border border-cyan-500/20">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-mono font-semibold text-slate-300">AGENT-01: ONLINE</span>
              <span className="text-xs font-mono text-cyan-400">Packaging Bay 1</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 overflow-x-auto py-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`relative flex items-center gap-2 rounded-md px-3.5 py-1.5 font-mono text-xs font-bold tracking-wider transition-all duration-300 ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/60 shadow-[0_0_15px_rgba(0,240,255,0.3)]'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400 animate-pulse' : 'text-slate-400'}`} />
                <span>{item.label}</span>
                {isActive && (
                  <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-cyan-400 shadow-[0_0_8px_#00f0ff]" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Live Simulation Control Player & Clock */}
        <div className="flex items-center gap-3">
          {/* Turn Scrub Controller */}
          <div className="flex items-center gap-2 rounded-lg bg-slate-950/80 p-1.5 border border-cyan-500/30 shadow-inner">
            <button
              onClick={() => factorymindData.stepBackward()}
              title="Step Backward"
              className="rounded p-1 text-slate-400 hover:bg-cyan-500/20 hover:text-cyan-300 transition"
            >
              <StepBack className="h-4 w-4" />
            </button>

            <button
              onClick={() => (isPlaying ? factorymindData.pause() : factorymindData.play())}
              title={isPlaying ? 'Pause Simulation' : 'Play Live Walkthrough'}
              className="flex items-center gap-1.5 rounded bg-cyan-500/20 px-2.5 py-1 font-mono text-xs font-bold text-cyan-300 border border-cyan-400/50 hover:bg-cyan-500/30 transition shadow-[0_0_10px_rgba(0,240,255,0.2)]"
            >
              {isPlaying ? <Pause className="h-3.5 w-3.5 text-cyan-400" /> : <Play className="h-3.5 w-3.5 text-cyan-400" />}
              <span>{isPlaying ? 'PAUSE' : 'REPLAY'}</span>
            </button>

            <button
              onClick={() => factorymindData.stepForward()}
              title="Step Forward"
              className="rounded p-1 text-slate-400 hover:bg-cyan-500/20 hover:text-cyan-300 transition"
            >
              <StepForward className="h-4 w-4" />
            </button>

            <div className="px-2 font-mono text-xs font-bold text-cyan-400 border-l border-slate-800">
              TURN <span className="text-white">{currentTurn}</span> / {totalTurns}
            </div>
          </div>

          {/* Clock Display */}
          <div className="hidden xl:flex items-center gap-2 rounded-md bg-slate-950/90 px-3 py-1.5 border border-slate-800 font-mono text-xs text-slate-300">
            <Clock className="h-3.5 w-3.5 text-cyan-400" />
            <span className="tracking-widest text-[11px] font-semibold text-cyan-300">{timeStr}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
