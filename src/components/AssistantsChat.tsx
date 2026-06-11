import { useState, useEffect, useRef } from "react";
import { ChatMessage, AgentInfo } from "../types";
import { Send, Bot, User, Sparkles, Loader2, BookOpen, AlertCircle, RefreshCw } from "lucide-react";

interface AssistantsChatProps {
  selectedCountyName?: string;
  onNavigateTab: (tab: any) => void;
  onSelectCounty: (code: string) => void;
}

export default function AssistantsChat({ selectedCountyName, onNavigateTab, onSelectCounty }: AssistantsChatProps) {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [activeAgentKey, setActiveAgentKey] = useState<string>("data");
  const [messages, setMessages] = useState<Record<string, ChatMessage[]>>({
    data: [
      { id: "1", sender: "agent", text: "Hello! I am your **Data Explorer Bot**. Ask me details about population estimates, GDP contributions, health index margins, or county availability log files! (e.g., *'Does Makueni have data?'*, *'Compare Nairobi and Mombasa'*).", timestamp: new Date().toLocaleTimeString() }
    ],
    prediction: [
      { id: "1", sender: "agent", text: "Welcome! I am your **Prediction Bot**. Ask me about machine learning models, developmental tier clustering (unsupervised K-Means), population forecasters, or Isolation Forest anomalies. (e.g., *'Kiambu population 2030'*, *'Explain development tiers'*).", timestamp: new Date().toLocaleTimeString() }
    ],
    guide: [
      { id: "1", sender: "agent", text: "Hi! I am your **Guide Bot**. I navigate the platform pages, spreadsheet downloads, Tableau templates, Power BI extracts, or Sunday 02:00 UTC scraping pipelines! (e.g., *'How to download CSV?'*, *'Tell me about n8n workflow'*).", timestamp: new Date().toLocaleTimeString() }
    ]
  });
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingAgents, setLoadingAgents] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Sync agents list on mount
  useEffect(() => {
    async function loadAgents() {
      try {
        setLoadingAgents(true);
        const res = await fetch("/api/v1/chat/agents");
        if (res.ok) {
          const json = await res.json();
          setAgents(json.agents);
        }
      } catch (err) {
        console.error("Unable to load agents list:", err);
      } finally {
        setLoadingAgents(false);
      }
    }
    loadAgents();
  }, []);

  // Scroll to bottom whenever messages list grows
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeAgentKey]);

  // Handle queries submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = inputValue.trim();
    if (!query || loading) return;

    // Add user message immediately
    const userMsg: ChatMessage = {
      id: Math.random().toString(),
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => ({
      ...prev,
      [activeAgentKey]: [...prev[activeAgentKey], userMsg]
    }));
    setInputValue("");
    setLoading(true);

    try {
      const res = await fetch("/api/v1/chat/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          query,
          agent: activeAgentKey
        })
      });

      if (!res.ok) {
        throw new Error("Analytics agent returned an internal error.");
      }

      const reply = await res.json();
      
      const agentMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: "agent",
        text: reply.answer || "Offline fallback answer calculations loaded.",
        timestamp: new Date().toLocaleTimeString(),
        citations: reply.citations || []
      };

      setMessages(prev => ({
        ...prev,
        [activeAgentKey]: [...prev[activeAgentKey], agentMsg]
      }));

    } catch (err: any) {
      console.error(err);
      const errMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: "agent",
        text: `⚠️ **API Communication Timeout**: Connection failed. Please check that you've run the server-side compiler or configured \`GEMINI_API_KEY\` inside your secrets list.\n\n*(Offline fallbacks are available by typing standard query terms).*`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => ({
        ...prev,
        [activeAgentKey]: [...prev[activeAgentKey], errMsg]
      }));
    } finally {
      setLoading(false);
    }
  };

  const handlePromptBubbleClick = (prompt: string) => {
    setInputValue(prompt);
  };

  const activeAgent = agents.find(a => a.key === activeAgentKey);
  const currentMessages = messages[activeAgentKey] || [];

  // Recommended prompt starters for ease of play
  const promptStarters: Record<string, string[]> = {
    data: [
      `Compare Nairobi and Mombasa`,
      `Does Makueni contain data?`,
      `What is the population of Kiambu?`,
      `Which county is highest GDP contribution?`
    ],
    prediction: [
      `What will Kiambu population be in 2030?`,
      `How does economic clustering work?`,
      `Tell me about Isolation Forest health anomalies`,
      `What does OLS regression tell us about labor?`
    ],
    guide: [
      `How do I download metrics as CSV?`,
      `Tell me about n8n scraper workflow`,
      `How do I use the interactive map?`,
      `Show Power BI or Tableau templates`
    ]
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[550px]">
      
      {/* 1. Left - Agent Selector Rail */}
      <div className="w-full lg:w-72 shrink-0 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 p-4 rounded-3xl flex flex-col justify-between">
        <div className="flex flex-col gap-4">
          <span className="text-[10px] font-mono font-bold text-gray-400 uppercase tracking-widest block leading-none select-none">Active AI Companions</span>
          
          <div className="flex flex-col gap-2">
            {loadingAgents ? (
              <div className="flex flex-col items-center justify-center py-10">
                <Loader2 className="w-5 h-5 animate-spin text-emerald-500" />
                <p className="text-[10px] font-mono text-gray-400 mt-2">Loading agents roster...</p>
              </div>
            ) : (
              agents.map(a => (
                <button
                  key={a.key}
                  onClick={() => {
                    setActiveAgentKey(a.key);
                    setInputValue("");
                  }}
                  id={`btn-agent-${a.key}`}
                  className={`text-left p-3.5 border rounded-2xl transition duration-150 flex items-start gap-3 ${
                    activeAgentKey === a.key 
                      ? 'bg-white dark:bg-gray-800 border-emerald-500/30 text-emerald-700 dark:text-emerald-400 font-medium shadow-sm' 
                      : 'bg-transparent border-transparent text-gray-600 dark:text-gray-400 hover:bg-white/50 dark:hover:bg-gray-800/50'
                  }`}
                >
                  <span className="text-xl shrink-0 select-none leading-none mt-0.5">{a.icon}</span>
                  <div>
                    <div className="text-xs font-bold leading-none">{a.name}</div>
                    <div className="text-[9px] text-gray-500 dark:text-gray-500 leading-normal mt-1 leading-tight">{a.description}</div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Status Indicator */}
        <div className="bg-white/80 dark:bg-black/20 border border-slate-100 dark:border-gray-900 px-4 py-3 rounded-2xl flex items-center gap-2.5">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <div className="text-[10px] font-mono text-gray-400">
            Engine: <span className="font-bold text-gray-200">Gemini 3.5 Flash</span>
          </div>
        </div>
      </div>

      {/* 2. Right - Messages Thread Screen */}
      <div className="flex-1 bg-white dark:bg-gray-950 border border-gray-100 dark:border-gray-900 rounded-3xl flex flex-col overflow-hidden shadow-sm">
        
        {/* Agent Header bar */}
        {activeAgent && (
          <div className="px-6 py-4 bg-slate-50/40 dark:bg-slate-900/10 border-b border-slate-100 dark:border-gray-900 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl select-none leading-none">{activeAgent.icon}</span>
              <div>
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-100">{activeAgent.name}</h4>
                <p className="text-[9px] text-gray-400 font-mono mt-0.5 uppercase tracking-wider">{activeAgent.key} microservices</p>
              </div>
            </div>

            <div className="hidden sm:flex items-center gap-1">
              <Sparkles className="w-4 h-4 text-amber-500 animate-pulse" />
              <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider font-semibold">Gemini API Online</span>
            </div>
          </div>
        )}

        {/* Messaging Timeline Container */}
        <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-4">
          {currentMessages.map((msg) => {
            const isAgent = msg.sender === 'agent';
            return (
              <div 
                key={msg.id} 
                className={`flex gap-3 max-w-[85%] ${isAgent ? 'self-start' : 'self-end flex-row-reverse'}`}
              >
                {/* Avatar Icon */}
                <div className={`w-8 h-8 rounded-xl shrink-0 flex items-center justify-center text-xs font-semibold ${isAgent ? 'bg-slate-50 border border-slate-100 dark:bg-slate-900 dark:border-gray-800 text-emerald-600' : 'bg-slate-900 text-white'}`}>
                  {isAgent ? <Bot className="w-4 h-4 text-emerald-600" /> : <User className="w-4 h-4 text-slate-100" />}
                </div>

                {/* Message Body Content bubble */}
                <div className="flex flex-col gap-1.5 matches-markdown">
                  <div 
                    className={`px-4 py-3 rounded-2xl text-[12px] leading-relaxed whitespace-pre-wrap ${
                      isAgent 
                        ? 'bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850 text-slate-800 dark:text-slate-100' 
                        : 'bg-emerald-600 text-white font-medium'
                    }`}
                  >
                    {/* Render simplified custom inline bold formatting cleanly */}
                    {msg.text.split("**").map((chunk, idx) => {
                      if (idx % 2 === 1) {
                        return <strong key={idx} className={isAgent ? "text-emerald-700 dark:text-emerald-400 font-bold" : "text-amber-300 font-bold"}>{chunk}</strong>;
                      }
                      return chunk;
                    })}
                  </div>

                  {/* Render citations labels if present */}
                  {isAgent && msg.citations && msg.citations.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 items-center select-none">
                      <BookOpen className="w-3 h-3 text-slate-400 shrink-0" />
                      <span className="text-[8px] font-mono text-slate-400 uppercase tracking-widest mr-1">Sources:</span>
                      {msg.citations.map((c, i) => (
                        <span key={i} className="text-[9px] font-mono bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-gray-500 rounded px-1.5 py-0.2">
                          {c}
                        </span>
                      ))}
                    </div>
                  )}

                  <span className="text-[8px] font-mono text-gray-400 self-start">{msg.timestamp}</span>
                </div>
              </div>
            );
          })}
          {loading && (
            <div className="flex gap-3 max-w-[85%] self-start">
              <div className="w-8 h-8 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-gray-800 flex items-center justify-center">
                <Bot className="w-4 h-4 text-emerald-600 animate-spin" />
              </div>
              <div className="bg-slate-50 dark:bg-slate-900 border border-slate-100 px-4 py-3 rounded-2xl text-xs font-mono text-gray-400 flex items-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-500" />
                Formulating analytical response...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompt starters bar */}
        <div className="px-6 py-2 border-t border-slate-50 dark:border-slate-900 bg-slate-50/20 dark:bg-slate-950/20 overflow-x-auto select-none flex items-center gap-2 max-w-full">
          <span className="text-[8px] font-mono text-slate-400 uppercase tracking-widest shrink-0">Prompts:</span>
          <div className="flex gap-2 shrink-0">
            {promptStarters[activeAgentKey]?.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handlePromptBubbleClick(p)}
                className="text-[10px] font-medium font-sans border border-slate-100 bg-white hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:hover:bg-slate-850 text-emerald-700 dark:text-emerald-400 px-3 py-1.5 rounded-full transition"
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Input box form */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-slate-100 dark:border-gray-900 flex gap-3 select-none">
          <input
            id="chat-input"
            type="text"
            placeholder={activeAgent ? `Ask ${activeAgent.name}...` : "Send query..."}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={loading}
            className="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-xs font-semibold rounded-2xl px-5 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <button
            id="chat-submit-btn"
            type="submit"
            disabled={!inputValue.trim() || loading}
            className="bg-slate-900 hover:bg-slate-850 dark:bg-white dark:hover:bg-slate-100 text-white dark:text-slate-900 p-3.5 rounded-2xl transition disabled:opacity-40 flex items-center justify-center shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

      </div>
    </div>
  );
}
