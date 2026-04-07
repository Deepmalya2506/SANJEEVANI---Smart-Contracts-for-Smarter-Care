import { motion } from "framer-motion";
import { LayoutDashboard, Store, BarChart3, Bot } from "lucide-react";
import logo from "@/assets/sanjeevani-logo.png";

const navItems = [
  { label: "Dashboard", icon: LayoutDashboard, active: true },
  { label: "Marketplace", icon: Store },
  { label: "Analytics", icon: BarChart3 },
  { label: "AI Assistant", icon: Bot },
];

const Navbar = ({ onAIClick }: { onAIClick: () => void }) => {
  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-50 glass-panel-strong border-b border-glass-border"
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
    >
      <div className="flex items-center justify-between px-4 md:px-8 h-16">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <img
            src={logo}
            alt="Sanjeevani"
            className="w-9 h-9 drop-shadow-[0_0_12px_hsl(280,70%,60%)]"
          />
          <span className="font-display text-lg tracking-[0.2em] glow-text text-foreground hidden sm:block">
            SANJEEVANI
          </span>
        </div>

        {/* Nav Items */}
        <div className="flex items-center gap-1">
          {navItems.map((item) => (
            <button
              key={item.label}
              onClick={item.label === "AI Assistant" ? onAIClick : undefined}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg font-body text-sm tracking-wide transition-all duration-300
                ${item.active
                  ? "bg-primary/20 text-foreground glow-border"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
                }`}
            >
              <item.icon className="w-4 h-4" />
              <span className="hidden md:inline">{item.label}</span>
            </button>
          ))}
        </div>

        {/* Status */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse-glow" />
          <span className="font-body text-xs tracking-wider text-muted-foreground hidden sm:block">
            SYSTEM ONLINE
          </span>
        </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;
