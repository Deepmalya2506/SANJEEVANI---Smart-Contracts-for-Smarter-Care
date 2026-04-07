import { motion } from "framer-motion";
import { Truck, Package, Shield, QrCode, Hash, Clock } from "lucide-react";

const statusSteps = [
  { label: "Request Initiated", time: "14:32:10", done: true },
  { label: "Escrow Locked", time: "14:32:15", done: true },
  { label: "Equipment Dispatched", time: "14:33:02", done: true },
  { label: "In Transit", time: "14:35:40", done: false, active: true },
  { label: "Delivered", time: "--:--:--", done: false },
];

const RightPanel = () => {
  return (
    <motion.div
      className="glass-panel p-5 flex flex-col gap-5 h-full overflow-y-auto scrollbar-hidden"
      initial={{ x: 60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.6, delay: 0.4, ease: [0.4, 0, 0.2, 1] }}
    >
      <h2 className="font-display text-sm tracking-[0.2em] text-foreground glow-text">
        LIVE STATUS
      </h2>

      {/* Status Badge */}
      <motion.div
        className="flex items-center gap-3 p-3 rounded-lg bg-primary/10 border border-primary/30"
        animate={{ boxShadow: ["0 0 10px hsl(280 70% 60% / 0.2)", "0 0 20px hsl(280 70% 60% / 0.4)", "0 0 10px hsl(280 70% 60% / 0.2)"] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <Truck className="w-5 h-5 text-glow-purple" />
        <div>
          <span className="font-display text-xs tracking-[0.15em] text-foreground">IN_TRANSIT</span>
          <p className="font-body text-xs text-muted-foreground">ETA: 8 minutes</p>
        </div>
      </motion.div>

      {/* Timeline */}
      <div className="space-y-1">
        <label className="font-body text-xs tracking-wider text-muted-foreground flex items-center gap-2">
          <Clock className="w-3 h-3" /> ACTIVITY LOG
        </label>
        <div className="relative pl-4 space-y-4 mt-3">
          <div className="absolute left-[7px] top-2 bottom-2 w-px bg-gradient-to-b from-primary via-accent to-muted" />
          {statusSteps.map((step, i) => (
            <motion.div
              key={step.label}
              className="relative flex items-start gap-3"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + i * 0.1 }}
            >
              <div className={`w-3.5 h-3.5 rounded-full border-2 -ml-[11px] mt-0.5 shrink-0
                ${step.done ? "bg-primary border-primary" : step.active ? "bg-transparent border-glow-purple animate-pulse-glow" : "bg-transparent border-muted"}`}
              />
              <div className="flex-1 min-w-0">
                <span className={`font-body text-sm block ${step.done || step.active ? "text-foreground" : "text-muted-foreground"}`}>
                  {step.label}
                </span>
                <span className="font-body text-xs text-muted-foreground">{step.time}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Blockchain / QR Section */}
      <div className="space-y-3 mt-auto">
        <label className="font-body text-xs tracking-wider text-muted-foreground flex items-center gap-2">
          <Shield className="w-3 h-3" /> VERIFICATION
        </label>

        <div className="glass-panel p-3 space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-16 h-16 rounded-lg bg-muted/40 border border-glass-border flex items-center justify-center">
              <QrCode className="w-10 h-10 text-glow-purple opacity-60" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-body text-xs text-muted-foreground">Transaction Hash</p>
              <p className="font-body text-xs text-foreground/80 truncate flex items-center gap-1">
                <Hash className="w-3 h-3 shrink-0" />
                0x7f2c...a3b1e8d4
              </p>
              <p className="font-body text-xs text-muted-foreground mt-1 flex items-center gap-1">
                <Package className="w-3 h-3" />
                Escrow: Locked
              </p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default RightPanel;
