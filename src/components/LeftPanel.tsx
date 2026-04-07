import { motion } from "framer-motion";
import { MapPin, Wind, HeartPulse, Clock, IndianRupee, Check } from "lucide-react";
import { useState } from "react";

const hospitals = [
  "AIIMS New Delhi",
  "Apollo Hospitals, Kolkata",
  "Medica Superspeciality",
  "Fortis Hospital, Bangalore",
];

const equipment = [
  { label: "Oxygen Cylinder", icon: Wind },
  { label: "Ventilator", icon: HeartPulse },
  { label: "Defibrillator", icon: HeartPulse },
];

const lenders = [
  { name: "MedSupply Hub", distance: "12 min", available: true, cost: "₹1,200/hr" },
  { name: "CareEquip Co.", distance: "15 min", available: true, cost: "₹950/hr" },
  { name: "LifeLine Med", distance: "22 min", available: false, cost: "₹1,400/hr" },
];

const LeftPanel = () => {
  const [selectedHospital, setSelectedHospital] = useState("");
  const [selectedEquip, setSelectedEquip] = useState("");

  return (
    <motion.div
      className="glass-panel p-5 flex flex-col gap-5 h-full overflow-y-auto scrollbar-hidden"
      initial={{ x: -60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.6, delay: 0.2, ease: [0.4, 0, 0.2, 1] }}
    >
      <h2 className="font-display text-sm tracking-[0.2em] text-foreground glow-text">
        REQUEST EQUIPMENT
      </h2>

      {/* Hospital Select */}
      <div className="space-y-2">
        <label className="font-body text-xs tracking-wider text-muted-foreground flex items-center gap-2">
          <MapPin className="w-3 h-3" /> SELECT HOSPITAL
        </label>
        <select
          value={selectedHospital}
          onChange={(e) => setSelectedHospital(e.target.value)}
          className="w-full bg-muted/50 border border-glass-border rounded-lg px-3 py-2.5 font-body text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary transition-all"
        >
          <option value="">Auto-detect nearby...</option>
          {hospitals.map((h) => (
            <option key={h} value={h}>{h}</option>
          ))}
        </select>
      </div>

      {/* Equipment Type */}
      <div className="space-y-2">
        <label className="font-body text-xs tracking-wider text-muted-foreground">
          EQUIPMENT TYPE
        </label>
        <div className="grid gap-2">
          {equipment.map((eq) => (
            <button
              key={eq.label}
              onClick={() => setSelectedEquip(eq.label)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border font-body text-sm transition-all duration-300
                ${selectedEquip === eq.label
                  ? "border-primary bg-primary/15 text-foreground glow-border"
                  : "border-glass-border bg-muted/20 text-muted-foreground hover:border-primary/50 hover:bg-muted/40"
                }`}
            >
              <eq.icon className="w-4 h-4" />
              {eq.label}
            </button>
          ))}
        </div>
      </div>

      {/* Nearby Lenders */}
      <div className="space-y-3">
        <label className="font-body text-xs tracking-wider text-muted-foreground">
          NEARBY LENDERS
        </label>
        {lenders.map((lender, i) => (
          <motion.div
            key={lender.name}
            className="glass-panel p-3 space-y-2"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + i * 0.1 }}
          >
            <div className="flex justify-between items-center">
              <span className="font-body text-sm text-foreground">{lender.name}</span>
              <span className={`flex items-center gap-1 text-xs font-body ${lender.available ? "text-green-400" : "text-destructive"}`}>
                {lender.available ? <Check className="w-3 h-3" /> : null}
                {lender.available ? "Available" : "Busy"}
              </span>
            </div>
            <div className="flex justify-between text-xs text-muted-foreground font-body">
              <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{lender.distance}</span>
              <span className="flex items-center gap-1"><IndianRupee className="w-3 h-3" />{lender.cost}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* CTA */}
      <motion.button
        className="btn-glow py-3 px-6 text-foreground mt-auto"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        ⚡ Request Now
      </motion.button>
    </motion.div>
  );
};

export default LeftPanel;
