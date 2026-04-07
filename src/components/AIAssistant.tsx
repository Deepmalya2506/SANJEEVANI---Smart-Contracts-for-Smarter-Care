import { motion, AnimatePresence } from "framer-motion";
import { Bot, X, Send, Mic, Sparkles } from "lucide-react";
import { useState } from "react";

const suggestions = [
  "Find oxygen within 15 minutes",
  "Request from nearest hospital",
  "Show available ventilators",
];

const AIAssistant = ({ isOpen, onToggle }: { isOpen: boolean; onToggle: () => void }) => {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: "assistant", content: "Namaste! I'm Sanjeevani AI. How can I assist you with emergency medical logistics today?" },
  ]);
  const [input, setInput] = useState("");

  const handleSend = (text?: string) => {
    const msg = text || input;
    if (!msg.trim()) return;
    setMessages((prev) => [
      ...prev,
      { role: "user", content: msg },
      { role: "assistant", content: `Searching medical network for "${msg}"... Found 3 matches within your area. Updating map view.` },
    ]);
    setInput("");
  };

  return (
    <>
      {/* Floating AI Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full btn-glow flex items-center justify-center"
            onClick={onToggle}
            initial={{ scale: 0 }}
            animate={{ scale: 1, y: [0, -6, 0] }}
            exit={{ scale: 0 }}
            transition={{ y: { duration: 2, repeat: Infinity, ease: "easeInOut" } }}
            whileHover={{ scale: 1.1 }}
          >
            <Bot className="w-6 h-6 text-foreground" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed right-0 top-16 bottom-0 w-full sm:w-96 z-40 glass-panel-strong border-l border-glass-border flex flex-col"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-glass-border">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-glow-purple" />
                </div>
                <div>
                  <span className="font-display text-xs tracking-[0.15em] text-foreground">SANJEEVANI AI</span>
                  <p className="font-body text-xs text-muted-foreground">MCP Assistant</p>
                </div>
              </div>
              <button onClick={onToggle} className="p-2 rounded-lg hover:bg-muted/40 transition-colors">
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto scrollbar-hidden p-4 space-y-3">
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <div
                    className={`max-w-[80%] px-4 py-2.5 rounded-2xl font-body text-sm
                      ${msg.role === "user"
                        ? "bg-primary/30 text-foreground rounded-br-sm"
                        : "bg-muted/50 text-foreground rounded-bl-sm border border-glass-border"
                      }`}
                    style={msg.role === "assistant" ? { boxShadow: "0 0 12px hsl(280 70% 60% / 0.1)" } : {}}
                  >
                    {msg.content}
                  </div>
                </motion.div>
              ))}

              {/* Suggestions */}
              {messages.length <= 1 && (
                <div className="space-y-2 mt-4">
                  <p className="font-body text-xs text-muted-foreground">Suggestions:</p>
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      onClick={() => handleSend(s)}
                      className="block w-full text-left px-3 py-2 rounded-lg border border-glass-border bg-muted/20 font-body text-sm text-muted-foreground hover:text-foreground hover:border-primary/40 hover:bg-muted/40 transition-all"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Input */}
            <div className="p-4 border-t border-glass-border">
              <div className="flex items-center gap-2 bg-muted/30 rounded-xl border border-glass-border px-3 py-2 focus-within:border-primary/50 transition-colors">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  placeholder="Ask Sanjeevani AI..."
                  className="flex-1 bg-transparent font-body text-sm text-foreground placeholder:text-muted-foreground outline-none"
                />
                <button className="p-1.5 rounded-lg hover:bg-muted/40 transition-colors">
                  <Mic className="w-4 h-4 text-muted-foreground" />
                </button>
                <button
                  onClick={() => handleSend()}
                  className="p-1.5 rounded-lg bg-primary/30 hover:bg-primary/50 transition-colors"
                >
                  <Send className="w-4 h-4 text-foreground" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default AIAssistant;
