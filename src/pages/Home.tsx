import { motion } from "framer-motion";
import { ArrowRight, Heart, Shield, Zap, Globe, Bot } from "lucide-react";
import { useNavigate } from "react-router-dom";
import VideoBackground from "@/components/VideoBackground";
import ParticleOverlay from "@/components/ParticleOverlay";
import AIAssistant from "@/components/AIAssistant";
import FluidText from "@/components/FluidText";
import { useState } from "react";

const features = [
  {
    icon: Zap,
    title: "Real-Time Logistics",
    description: "AI-powered routing delivers critical medical equipment within minutes, not hours.",
  },
  {
    icon: Shield,
    title: "Blockchain Verified",
    description: "Every transaction is escrow-locked and verified on-chain for complete transparency.",
  },
  {
    icon: Globe,
    title: "Pan-India Network",
    description: "Connected to 10,000+ hospitals and suppliers across the nation.",
  },
  {
    icon: Heart,
    title: "Lives Saved",
    description: "Reducing emergency response time by 60% through intelligent resource matching.",
  },
];

const fadeVariant = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 1, ease: "easeOut" } },
};

const Home = () => {
  const navigate = useNavigate();
  const [aiOpen, setAiOpen] = useState(false);

  return (
    <div className="h-screen w-screen overflow-y-auto overflow-x-hidden relative">
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
            <span className="font-display text-lg tracking-[0.15em] text-foreground">
              Sanjeevani
            </span>
          </div>
          <div className="flex items-center gap-1">
            {["Home", "Dashboard", "Marketplace", "Analytics"].map((item) => (
              <button
                key={item}
                onClick={() => {
                  if (item === "Home") return;
                  if (item === "Dashboard") navigate("/dashboard");
                  if (item === "Marketplace") navigate("/marketplace");
                  if (item === "Analytics") navigate("/analytics");
                }}
                className={`px-3 py-2 rounded-xl font-body text-sm tracking-wide transition-all duration-300
                  ${item === "Home"
                    ? "bg-primary/20 text-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
                  }`}
              >
                <span className="hidden md:inline">{item}</span>
                <span className="md:hidden text-xs">{item.slice(0, 4)}</span>
              </button>
            ))}
          </div>
        </div>
      </motion.nav>

      {/* Hero */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6 text-center">
        <FluidText />

        <motion.p
          className="font-body text-lg md:text-2xl text-muted-foreground tracking-wider mb-4 max-w-2xl"
          variants={fadeVariant}
          initial="hidden"
          animate="visible"
          transition={{ delay: 0.6, duration: 1 }}
        >
          AI-Powered Emergency Medical Logistics
        </motion.p>

        <motion.p
          className="font-body text-sm md:text-base text-muted-foreground/70 max-w-xl mb-10 leading-relaxed"
          variants={fadeVariant}
          initial="hidden"
          animate="visible"
          transition={{ delay: 1.0, duration: 1 }}
        >
          Connecting hospitals, suppliers, and emergency responders through intelligent
          real-time logistics — saving lives when every second counts.
        </motion.p>

        <motion.div
          className="flex flex-col sm:flex-row gap-4"
          variants={fadeVariant}
          initial="hidden"
          animate="visible"
          transition={{ delay: 1.4, duration: 0.8 }}
        >
          <motion.button
            className="btn-glow py-3 px-8 text-foreground flex items-center gap-2"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate("/dashboard")}
          >
            Open Dashboard <ArrowRight className="w-4 h-4" />
          </motion.button>
          <motion.button
            className="py-3 px-8 rounded-xl glass-panel text-foreground font-body text-sm tracking-wider hover:bg-muted/40 transition-all flex items-center gap-2"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => setAiOpen(true)}
          >
            <Bot className="w-4 h-4" /> Talk to AI
          </motion.button>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          className="absolute bottom-8 flex flex-col items-center gap-2"
          animate={{ opacity: [0.3, 0.7, 0.3] }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          <span className="font-body text-xs text-muted-foreground/50 tracking-widest">SCROLL</span>
          <div className="w-px h-8 bg-gradient-to-b from-muted-foreground/30 to-transparent" />
        </motion.div>
      </div>

      {/* About Section */}
      <div className="relative z-10 py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 1.2 }}
          >
            <span className="font-body text-xs tracking-[0.3em] text-primary mb-4 block uppercase">About</span>
            <h2
              className="text-2xl md:text-4xl text-foreground mb-6"
             
            >
              Healing Through Technology
            </h2>
            <p className="font-body text-base md:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Sanjeevani bridges the gap between medical emergencies and timely equipment delivery.
              Inspired by Ayurveda's philosophy of holistic healing and modern AI innovation,
              we've built a platform that ensures no hospital is ever left without critical resources.
            </p>
          </motion.div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                className="glass-panel p-6 group hover:border-primary/40 transition-all duration-500"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ delay: i * 0.15, duration: 0.8 }}
              >
                <div className="w-10 h-10 rounded-xl bg-primary/15 flex items-center justify-center mb-4 group-hover:bg-primary/25 transition-colors">
                  <feature.icon className="w-5 h-5 text-primary" />
                </div>
                <h3 className="font-body text-sm font-semibold tracking-wide text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="font-body text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="relative z-10 py-16 px-6">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { value: "10K+", label: "Hospitals" },
            { value: "60%", label: "Faster Response" },
            { value: "24/7", label: "AI Monitoring" },
            { value: "99.9%", label: "Uptime" },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              className="text-center"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15, duration: 0.8 }}
            >
              <span
                className="text-2xl md:text-3xl text-foreground"
               
              >
                {stat.value}
              </span>
              <p className="font-body text-xs text-muted-foreground tracking-wider mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="relative z-10 py-12 px-6 border-t border-glass-border/30">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <span
            className="text-sm text-muted-foreground"
           
          >
            Sanjeevani
          </span>
          <p className="font-body text-xs text-muted-foreground/60">
            © 2026 Sanjeevani. AI-powered emergency medical logistics.
          </p>
        </div>
      </div>

      <AIAssistant isOpen={aiOpen} onToggle={() => setAiOpen((v) => !v)} />
    </div>
  );
};

export default Home;
