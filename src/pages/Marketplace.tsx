import { motion } from "framer-motion";
import { Search, Filter, Wind, HeartPulse, Stethoscope, Syringe, Star, MapPin, IndianRupee, ArrowLeft } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import VideoBackground from "@/components/VideoBackground";
import ParticleOverlay from "@/components/ParticleOverlay";
import AIAssistant from "@/components/AIAssistant";
import logo from "@/assets/sanjeevani-logo.png";

const categories = [
  { label: "All", icon: Filter },
  { label: "Oxygen", icon: Wind },
  { label: "Ventilators", icon: HeartPulse },
  { label: "Diagnostics", icon: Stethoscope },
  { label: "Consumables", icon: Syringe },
];

const listings = [
  { name: "Portable Oxygen Concentrator", category: "Oxygen", supplier: "MedEquip India", location: "Delhi NCR", price: "₹800/hr", rating: 4.8, available: true, eta: "12 min" },
  { name: "ICU Ventilator V500", category: "Ventilators", supplier: "CareEquip Co.", location: "Kolkata", price: "₹2,500/hr", rating: 4.9, available: true, eta: "18 min" },
  { name: "Pulse Oximeter Pro", category: "Diagnostics", supplier: "HealthTech Labs", location: "Mumbai", price: "₹150/hr", rating: 4.5, available: true, eta: "8 min" },
  { name: "Oxygen Cylinder (10L)", category: "Oxygen", supplier: "LifeLine Med", location: "Bangalore", price: "₹1,200/hr", rating: 4.7, available: false, eta: "25 min" },
  { name: "BiPAP Machine", category: "Ventilators", supplier: "Apollo Supply", location: "Chennai", price: "₹1,800/hr", rating: 4.6, available: true, eta: "15 min" },
  { name: "Digital Stethoscope", category: "Diagnostics", supplier: "MedSupply Hub", location: "Hyderabad", price: "₹300/hr", rating: 4.4, available: true, eta: "10 min" },
  { name: "IV Infusion Set (50 units)", category: "Consumables", supplier: "SurgiCare", location: "Pune", price: "₹500/pack", rating: 4.3, available: true, eta: "20 min" },
  { name: "Nebulizer Machine", category: "Oxygen", supplier: "BreathEasy", location: "Jaipur", price: "₹400/hr", rating: 4.6, available: true, eta: "14 min" },
];

const Marketplace = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [aiOpen, setAiOpen] = useState(false);

  const filtered = listings.filter((item) => {
    const matchesCategory = activeCategory === "All" || item.category === activeCategory;
    const matchesSearch = item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.supplier.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  });

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
            <span className="text-sm tracking-[0.15em] text-foreground hidden sm:block">Sanjeevani</span>
          </div>
          <div className="flex items-center gap-1">
            {["Home", "Dashboard", "Marketplace", "Analytics"].map((item) => (
              <button
                key={item}
                onClick={() => {
                  if (item === "Home") navigate("/");
                  if (item === "Dashboard") navigate("/dashboard");
                  if (item === "Marketplace") return;
                  if (item === "Analytics") navigate("/analytics");
                }}
                className={`px-3 py-2 rounded-xl font-body text-sm tracking-wide transition-all duration-300
                  ${item === "Marketplace"
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

      {/* Content */}
      <div className="relative z-10 flex-1 pt-20 px-4 md:px-8 pb-4 overflow-y-auto scrollbar-hidden">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <motion.div
            className="mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="font-display text-xl md:text-2xl tracking-[0.2em] text-foreground glow-text mb-2">
              MARKETPLACE
            </h1>
            <p className="font-body text-sm text-muted-foreground">Browse and request medical equipment from verified suppliers</p>
          </motion.div>

          {/* Search & Filter */}
          <motion.div
            className="flex flex-col sm:flex-row gap-3 mb-6"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.5 }}
          >
            <div className="flex-1 flex items-center gap-2 glass-panel px-4 py-2.5">
              <Search className="w-4 h-4 text-muted-foreground shrink-0" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search equipment or supplier..."
                className="flex-1 bg-transparent font-body text-sm text-foreground placeholder:text-muted-foreground outline-none"
              />
            </div>
            <div className="flex gap-2 overflow-x-auto scrollbar-hidden">
              {categories.map((cat) => (
                <button
                  key={cat.label}
                  onClick={() => setActiveCategory(cat.label)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg font-body text-xs tracking-wide whitespace-nowrap transition-all
                    ${activeCategory === cat.label
                      ? "bg-primary/20 text-foreground border border-primary/40"
                      : "bg-muted/20 text-muted-foreground border border-glass-border hover:bg-muted/40"
                    }`}
                >
                  <cat.icon className="w-3.5 h-3.5" />
                  {cat.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* Listings Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filtered.map((item, i) => (
              <motion.div
                key={item.name}
                className="glass-panel p-4 flex flex-col gap-3 hover:border-primary/40 transition-all duration-300 group"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * i, duration: 0.4 }}
              >
                <div className="flex items-start justify-between">
                  <span className="font-body text-xs px-2 py-0.5 rounded-full bg-primary/15 text-primary border border-primary/20">
                    {item.category}
                  </span>
                  <span className={`text-xs font-body ${item.available ? "text-green-400" : "text-destructive"}`}>
                    {item.available ? "● Available" : "● Busy"}
                  </span>
                </div>
                <h3 className="font-body text-sm text-foreground font-semibold leading-tight">{item.name}</h3>
                <p className="font-body text-xs text-muted-foreground">{item.supplier}</p>
                <div className="flex items-center gap-3 text-xs text-muted-foreground font-body">
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{item.location}</span>
                  <span className="flex items-center gap-1"><Star className="w-3 h-3 text-yellow-400" />{item.rating}</span>
                </div>
                <div className="flex items-center justify-between mt-auto pt-2 border-t border-glass-border/50">
                  <span className="font-body text-sm text-foreground flex items-center gap-1">
                    <IndianRupee className="w-3 h-3" />{item.price}
                  </span>
                  <span className="font-body text-xs text-muted-foreground">ETA: {item.eta}</span>
                </div>
                <motion.button
                  className="btn-glow py-2 px-4 text-foreground text-xs w-full opacity-80 group-hover:opacity-100 transition-opacity"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  disabled={!item.available}
                >
                  {item.available ? "⚡ Request Now" : "Unavailable"}
                </motion.button>
              </motion.div>
            ))}
          </div>

          {filtered.length === 0 && (
            <div className="text-center py-20">
              <p className="font-body text-muted-foreground">No equipment found matching your criteria.</p>
            </div>
          )}
        </div>
      </div>

      <AIAssistant isOpen={aiOpen} onToggle={() => setAiOpen((v) => !v)} />
    </div>
  );
};

export default Marketplace;
