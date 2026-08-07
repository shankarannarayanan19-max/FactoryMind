import { useEffect, useState } from 'react';
import { ParticleBackground } from './components/ParticleBackground';
import { Navbar } from './components/Navbar';
import { HomeDashboard } from './components/HomeDashboard';
import { InteractiveFactoryMap } from './components/InteractiveFactoryMap';
import { WorldModelExplorer } from './components/WorldModelExplorer';
import { ObjectInspector } from './components/ObjectInspector';
import { MissionTimeline } from './components/MissionTimeline';
import { MemoryVisualization } from './components/MemoryVisualization';
import { QueryInterface } from './components/QueryInterface';
import { LiveEventFeed } from './components/LiveEventFeed';
import { ReportScreen } from './components/ReportScreen';
import type { ScenarioTurnState } from './types/factorymind';
import { factorymindData } from './services/factorymindData';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [selectedObjectId, setSelectedObjectId] = useState<string | null>(null);
  const [currentState, setCurrentState] = useState<ScenarioTurnState>(factorymindData.getCurrentState());
  const [highlightedRoomId, setHighlightedRoomId] = useState<string | undefined>(undefined);

  useEffect(() => {
    const unsubscribe = factorymindData.subscribe(() => {
      setCurrentState(factorymindData.getCurrentState());
    });
    return () => unsubscribe();
  }, []);

  const handleOpenInspector = (id: string) => {
    setSelectedObjectId(id);
  };

  const handleCloseInspector = () => {
    setSelectedObjectId(null);
  };

  const handleHighlightTarget = (roomId?: string, assetId?: string) => {
    setHighlightedRoomId(roomId);
    if (assetId) {
      setSelectedObjectId(assetId);
    }
  };

  return (
    <div className="relative min-w-full min-h-screen bg-[#050811] text-slate-100 font-sans selection:bg-cyan-500 selection:text-black overflow-x-hidden">
      {/* Particle HUD Background */}
      <ParticleBackground />

      {/* Futuristic Scanline Layer */}
      <div className="scanline-overlay fixed inset-0 z-20 pointer-events-none" />

      {/* Main Container */}
      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Top HUD Bar */}
        <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Content Viewport */}
        <main className="flex-1 max-w-[1600px] w-full mx-auto p-4 md:p-6 space-y-6">
          {/* Active Tab View */}
          {activeTab === 'dashboard' && (
            <HomeDashboard
              state={currentState}
              setActiveTab={setActiveTab}
              onOpenInspector={handleOpenInspector}
            />
          )}

          {activeTab === 'map' && (
            <InteractiveFactoryMap
              state={currentState}
              onOpenInspector={handleOpenInspector}
              highlightedRoomId={highlightedRoomId}
            />
          )}

          {activeTab === 'graph' && (
            <WorldModelExplorer
              state={currentState}
              onOpenInspector={handleOpenInspector}
            />
          )}

          {activeTab === 'memory' && (
            <MemoryVisualization state={currentState} />
          )}

          {activeTab === 'query' && (
            <QueryInterface
              state={currentState}
              onHighlightTarget={handleHighlightTarget}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'report' && (
            <ReportScreen state={currentState} />
          )}

          {/* Always Visible Live Execution Pipeline Timeline */}
          <MissionTimeline state={currentState} />

          {/* Always Visible Live Event Taxonomy Feed */}
          <LiveEventFeed state={currentState} />
        </main>

        {/* Slide-Over Object Inspector Modal */}
        <ObjectInspector
          objectId={selectedObjectId}
          state={currentState}
          onClose={handleCloseInspector}
        />

        {/* Footer */}
        <footer className="relative z-30 hud-panel border-t border-slate-800 bg-[#050914] px-6 py-3 font-mono text-xs text-slate-500 flex flex-wrap items-center justify-between">
          <span>FACTORYMIND // PERSISTENT AI WORLD MODEL FOR AUTONOMOUS AGENTS</span>
          <span className="text-cyan-400">STATUS: RECONCILED STATE-OF-TRUTH</span>
        </footer>
      </div>
    </div>
  );
}

export default App;
