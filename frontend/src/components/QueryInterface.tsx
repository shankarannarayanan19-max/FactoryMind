import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Cpu,
  MapPin,
  MessageSquare,
  Send,
  Sparkles
} from 'lucide-react';
import type { ChatMessage, ScenarioTurnState } from '../types/factorymind';
import { factorymindData } from '../services/factorymindData';

interface QueryInterfaceProps {
  state: ScenarioTurnState;
  onHighlightTarget: (roomId?: string, assetId?: string) => void;
  setActiveTab: (tab: string) => void;
}

export const QueryInterface: React.FC<QueryInterfaceProps> = ({
  onHighlightTarget,
  setActiveTab
}) => {
  const [queryInput, setQueryInput] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-init',
      sender: 'FACTORYMIND_AI',
      text: 'Greetings. I am FactoryMind Query Router. Ask any natural language question regarding asset location, telemetry health, safety conditions, or historical state changes.',
      timestamp: '01:38:00'
    }
  ]);

  const handleSend = (textToSend?: string) => {
    const qText = textToSend || queryInput;
    if (!qText.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg-user-${Date.now()}`,
      sender: 'USER',
      text: qText,
      timestamp: new Date().toLocaleTimeString()
    };

    const aiMsg = factorymindData.processQuery(qText);

    setMessages((prev) => [...prev, userMsg, aiMsg]);
    if (!textToSend) setQueryInput('');

    // Trigger map/graph highlights if query targeted room or asset
    if (aiMsg.target_room || aiMsg.target_id) {
      onHighlightTarget(aiMsg.target_room, aiMsg.target_id);
    }
  };

  const samplePrompts = [
    'Where is CV-M02?',
    'Is CV-M02 abnormal?',
    'Is ROOM-PACK-01 safe?',
    'What objects are inside Packaging Bay 1?'
  ];

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
            <MessageSquare className="h-5 w-5 text-cyan-400 animate-pulse" />
            <h2 className="font-mono text-xl font-extrabold text-white glow-text-cyan tracking-wider">
              NATURAL LANGUAGE QUERY INTERFACE (§14)
            </h2>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            PURE STRUCTURAL GRAPH TRAVERSAL & EXPLAINABLE NARRATION ENGINE
          </p>
        </div>

        <span className="flex items-center gap-1.5 rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-mono text-cyan-400 border border-cyan-400/30">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400 animate-spin" />
          ZERO LLM FOR STRUCTURAL LOOKUPS
        </span>
      </div>

      {/* Main Chat Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Chat History Panel */}
        <div className="lg:col-span-8 flex flex-col h-[520px] rounded-xl bg-slate-950/90 border border-slate-800 p-4">
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {messages.map((msg) => {
              const isUser = msg.sender === 'USER';
              return (
                <motion.div
                  key={msg.id}
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {!isUser && (
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-950 border border-cyan-400/50 shadow-[0_0_10px_#00f0ff] shrink-0">
                      <Cpu className="h-4 w-4 text-cyan-400" />
                    </div>
                  )}

                  <div className={`max-w-xl rounded-xl p-4 font-mono text-xs ${
                    isUser
                      ? 'bg-cyan-950/40 text-cyan-200 border border-cyan-400/50'
                      : 'bg-slate-900/90 text-slate-200 border border-slate-800 shadow-lg'
                  }`}>
                    <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1 border-b border-slate-800/80 pb-1">
                      <span className="font-bold text-cyan-400">{msg.sender}</span>
                      <span>{msg.timestamp}</span>
                    </div>

                    <p className="font-sans leading-relaxed text-sm pt-1">{msg.text}</p>

                    {msg.source && (
                      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800 text-[10px]">
                        <span className="text-slate-500">SOURCE: {msg.source}</span>
                        {msg.target_room && (
                          <button
                            onClick={() => {
                              onHighlightTarget(msg.target_room, msg.target_id);
                              setActiveTab('map');
                            }}
                            className="flex items-center gap-1 text-cyan-400 hover:underline font-bold"
                          >
                            <MapPin className="h-3 w-3" />
                            <span>HIGHLIGHT ON MAP</span>
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Input Controls */}
          <div className="pt-3 border-t border-slate-800 flex gap-2">
            <input
              type="text"
              placeholder="Ask FactoryMind (e.g., 'Where is CV-M02?' or 'Is area safe?')..."
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              className="flex-1 bg-slate-900/90 border border-slate-800 rounded-lg px-4 py-2.5 font-mono text-xs text-cyan-300 focus:outline-none focus:border-cyan-400"
            />
            <button
              onClick={() => handleSend()}
              className="flex items-center gap-2 rounded-lg bg-cyan-500/20 px-5 py-2.5 font-mono text-xs font-bold text-cyan-300 border border-cyan-400/50 hover:bg-cyan-500/30 transition shadow-[0_0_10px_rgba(0,240,255,0.2)]"
            >
              <span>SEND</span>
              <Send className="h-3.5 w-3.5 text-cyan-400" />
            </button>
          </div>
        </div>

        {/* Sample Prompt Shortcuts & Graph Proof */}
        <div className="lg:col-span-4 hud-panel rounded-xl p-5 border-slate-800 flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="font-mono text-sm font-bold text-white tracking-wider uppercase flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan-400" />
              QUICK PROMPT SHORTCUTS
            </h3>

            <div className="space-y-2">
              {samplePrompts.map((promptText, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(promptText)}
                  className="w-full text-left p-3 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-cyan-400/50 hover:bg-cyan-950/20 font-mono text-xs text-slate-300 transition flex items-center justify-between group"
                >
                  <span>{promptText}</span>
                  <Send className="h-3.5 w-3.5 text-slate-500 group-hover:text-cyan-400 transition" />
                </button>
              ))}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs space-y-2 mt-4">
            <span className="text-cyan-400 font-bold block mb-1">PROVENANCE & DETERMINISM</span>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              Queries use direct structural dict/graph lookups over the WorldModel. Answers are verified against known ontology registrations with zero hallucination.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
