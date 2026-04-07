import { motion } from "framer-motion";
import { BarChart3, TrendingUp, Activity, Clock, Package, Heart, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import VideoBackground from "@/components/VideoBackground";
import ParticleOverlay from "@/components/ParticleOverlay";
import AIAssistant from "@/components/AIAssistant";
import logo from "@/assets/sanjeevani-logo.png";

const stats = [
  { label: "Total Requests", value: "12,847", change: "+12.5%", up: true, icon: Package },
  { label: "Avg Response Time", value: "14.2 min", change: "-8.3%", up: true, icon: Clock },
  { label: "Lives Impacted", value: "8,421", change: "+23.1%", up: true, icon: Heart },
  { label: "Active Suppliers", value: "1,234", change: "+5.7%", up: true, icon: Activity },
];

const weeklyData = [
  { day: "Mon", requests: 145, fulfilled: 138 },
  { day: "Tue", requests: 132, fulfilled: 128 },
  { day: "Wed", requests: 168, fulfilled: 161 },
  { day: "Thu", requests: 154, fulfilled: 149 },
  { day: "Fri", requests: 189, fulfilled: 182 },
  { day: "Sat", requests: 112, fulfilled: 108 },
  { day: "Sun", requests: 98, fulfilled: 95 },
];

const topEquipment = [
  { name: "Oxygen Concentrator", requests: 3240, pct: 85 },
  { name: "ICU Ventilator", requests: 2180, pct: 72 },
  { name: "Pulse Oximeter", requests: 1890, pct: 65 },
  { name: "Defibrillator", requests: 1420, pct: 55 },
  { name: "Nebulizer", requests: 980, pct: 40 },
];

const recentActivity = [
  { time: "2 min ago", event: "Oxygen delivered to AIIMS Delhi", type: "success" },
  { time: "8 min ago", event: "Ventilator request from Apollo Kolkata", type: "pending" },
  { time: "15 min ago", event: "Escrow released — ₹12,000", type: "transaction" },
  { time: "22 min ago", event: "New supplier registered: MedTech Pune", type: "info" },
  { time: "35 min ago", event: "Route optimized: 18min → 12min", type: "success" },
  { time: "1 hr ago", event: "Defibrillator dispatched to Fortis BLR", type: "pending" },
];

const maxRequests = Math.max(...weeklyData.map((d) => d.requests));

const Analytics = () => {
  const navigate = useNavigate();
  const [aiOpen, setAiOpen] = useState(false);

  return (
    <div className="h-screen w-screen overflow-hidden relative flex flex-col">
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
            <span className="font-body text-sm tracking-[0.2em] text-foreground hidden sm:block">Sanjeevani</span>
          </div>
          <div className="flex items-center gap-1">
            {["Home", "Dashboard", "Marketplace", "Analytics"].map((item) => (
              <button
                key={item}
                onClick={() => {
                  if (item === "Home") navigate("/");
                  if (item === "Dashboard") navigate("/dashboard");
                  if (item === "Marketplace") navigate("/marketplace");
                  if (item === "Analytics") return;
                }}
                className={`px-3 py-2 rounded-xl font-body text-sm tracking-wide transition-all duration-300
                  ${item === "Analytics"
                    ? "bg-primary/20 text-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
                  }`}
              >
                <span className="hidden md:inline">{item}</span>
              </button>
            ))}
          </div>
        </div>
      </motion.nav>

      {/* Content — inner glass screen */}
      <div className="relative z-10 flex-1 pt-20 px-3 md:px-6 pb-3 overflow-hidden flex items-stretch">
        <motion.div
          className="glass-screen flex-1 p-4 md:p-6 overflow-y-auto scrollbar-hidden"
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
        >
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <motion.div className="mb-6" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
              <h1
                className="text-xl md:text-2xl text-foreground mb-2"
               
              >
                Analytics
              </h1>
              <p className="font-body text-sm text-muted-foreground">Real-time platform performance and impact metrics</p>
            </motion.div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {stats.map((stat, i) => (
                <motion.div
                  key={stat.label}
                  className="glass-panel p-4"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1 + i * 0.05 }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <stat.icon className="w-4 h-4 text-primary" />
                    <span className={`flex items-center gap-0.5 text-xs font-body ${stat.up ? "text-green-400" : "text-destructive"}`}>
                      {stat.up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      {stat.change}
                    </span>
                  </div>
                  <p className="text-lg md:text-xl text-foreground">{stat.value}</p>
                  <p className="font-body text-xs text-muted-foreground">{stat.label}</p>
                </motion.div>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Chart */}
              <motion.div className="glass-panel p-5 lg:col-span-2" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-body text-xs tracking-[0.15em] text-foreground font-semibold uppercase">Weekly Overview</h3>
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1 font-body text-xs text-primary"><span className="w-2 h-2 rounded-full bg-primary" /> Requests</span>
                    <span className="flex items-center gap-1 font-body text-xs text-green-400"><span className="w-2 h-2 rounded-full bg-green-400" /> Fulfilled</span>
                  </div>
                </div>
                <div className="flex items-end gap-3 h-48">
                  {weeklyData.map((d, i) => (
                    <div key={d.day} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full flex gap-1 items-end h-40">
                        <motion.div className="flex-1 rounded-t-md bg-primary/40" initial={{ height: 0 }} animate={{ height: `${(d.requests / maxRequests) * 100}%` }} transition={{ delay: 0.3 + i * 0.05, duration: 0.6 }} />
                        <motion.div className="flex-1 rounded-t-md bg-green-400/40" initial={{ height: 0 }} animate={{ height: `${(d.fulfilled / maxRequests) * 100}%` }} transition={{ delay: 0.35 + i * 0.05, duration: 0.6 }} />
                      </div>
                      <span className="font-body text-xs text-muted-foreground">{d.day}</span>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Activity Feed */}
              <motion.div className="glass-panel p-5" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
                <h3 className="font-body text-xs tracking-[0.15em] text-foreground font-semibold uppercase mb-4">Live Activity</h3>
                <div className="space-y-3">
                  {recentActivity.map((item, i) => (
                    <motion.div key={i} className="flex gap-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 + i * 0.05 }}>
                      <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                        item.type === "success" ? "bg-green-400" :
                        item.type === "pending" ? "bg-yellow-400" :
                        item.type === "transaction" ? "bg-primary" : "bg-muted-foreground"
                      }`} />
                      <div className="min-w-0">
                        <p className="font-body text-sm text-foreground leading-tight">{item.event}</p>
                        <p className="font-body text-xs text-muted-foreground">{item.time}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </div>

            {/* Top Equipment */}
            <motion.div className="glass-panel p-5 mt-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
              <h3 className="font-body text-xs tracking-[0.15em] text-foreground font-semibold uppercase mb-4">Top Requested Equipment</h3>
              <div className="space-y-3">
                {topEquipment.map((eq, i) => (
                  <div key={eq.name} className="flex items-center gap-4">
                    <span className="font-body text-sm text-foreground w-40 shrink-0">{eq.name}</span>
                    <div className="flex-1 h-2 rounded-full bg-muted/40 overflow-hidden">
                      <motion.div className="h-full rounded-full bg-gradient-to-r from-primary to-accent" initial={{ width: 0 }} animate={{ width: `${eq.pct}%` }} transition={{ delay: 0.5 + i * 0.05, duration: 0.8 }} />
                    </div>
                    <span className="font-body text-xs text-muted-foreground w-16 text-right">{eq.requests.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>

      <AIAssistant isOpen={aiOpen} onToggle={() => setAiOpen((v) => !v)} />
    </div>
  );
};

export default Analytics;
