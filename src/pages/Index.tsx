import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import LoadingScreen from "@/components/LoadingScreen";
import LeftPanel from "@/components/LeftPanel";
import CenterMap from "@/components/CenterMap";
import RightPanel from "@/components/RightPanel";
import AIAssistant from "@/components/AIAssistant";
import VideoBackground from "@/components/VideoBackground";
import ParticleOverlay from "@/components/ParticleOverlay";
import logo from "@/assets/sanjeevani-logo.png";

const Index = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [aiOpen, setAiOpen] = useState(false);

  const handleLoadingComplete = useCallback(() => setLoading(false), []);

  return (
    <div className="h-screen w-screen overflow-hidden relative">
      <AnimatePresence mode="wait">
        {loading && <LoadingScreen key="loader" onComplete={handleLoadingComplete} />}
      </AnimatePresence>

      {!loading && (
        <>
          <VideoBackground />
          <ParticleOverlay />

          {/* Navbar */}
          <motion.nav
            className="fixed top-0 left-0 right-0 z-50 glass-panel-strong !rounded-none border-0 border-b"
            initial={{ y: -80 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="flex items-center justify-between px-6 md:px-12 h-16">
              <div className="flex items-center gap-3">
                <img src={logo} alt="Sanjeevani" className="w-8 h-8 rounded-full drop-shadow-[0_0_12px_hsl(280,70%,60%)]" />
                <span className="text-sm tracking-[0.15em] text-foreground hidden sm:block">Sanjeevani</span>
              </div>
              <div className="flex items-center gap-1">
                {["Home", "Dashboard", "Marketplace", "Analytics"].map((item) => (
                  <button
                    key={item}
                    onClick={() => {
                      if (item === "Home") navigate("/");
                      if (item === "Dashboard") return;
                      if (item === "Marketplace") navigate("/marketplace");
                      if (item === "Analytics") navigate("/analytics");
                    }}
                    className={`px-3 py-2 rounded-xl font-body text-sm tracking-wide transition-all duration-300
                      ${item === "Dashboard"
                        ? "bg-primary/20 text-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
                      }`}
                  >
                    <span className="hidden md:inline">{item}</span>
                    <span className="md:hidden text-xs">{item.slice(0, 4)}</span>
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                <span className="font-body text-xs tracking-wider text-muted-foreground hidden sm:block">ONLINE</span>
              </div>
            </div>
          </motion.nav>

          <div className="relative z-10 h-full flex flex-col">
            <div className="flex-1 pt-16 p-3 md:p-4 lg:p-5">
              <div className="h-full grid grid-cols-1 lg:grid-cols-[320px_1fr_320px] gap-3 md:gap-4">
                <div className="hidden lg:block"><LeftPanel /></div>
                <CenterMap />
                <div className="hidden lg:block"><RightPanel /></div>
              </div>
            </div>
          </div>

          <AIAssistant isOpen={aiOpen} onToggle={() => setAiOpen((v) => !v)} />
        </>
      )}
    </div>
  );
};

export default Index;
