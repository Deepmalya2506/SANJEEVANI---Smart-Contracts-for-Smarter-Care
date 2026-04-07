import { motion } from "framer-motion";
import { useEffect, useRef } from "react";

const hospitals = [
  { name: "AIIMS Delhi", x: 45, y: 35, pulse: true },
  { name: "Apollo Kolkata", x: 72, y: 42, pulse: true },
  { name: "Medica Super", x: 68, y: 48, pulse: false },
  { name: "Fortis Bangalore", x: 38, y: 68, pulse: true },
  { name: "CMC Vellore", x: 42, y: 72, pulse: false },
];

const connections = [
  { from: 0, to: 1 },
  { from: 1, to: 2 },
  { from: 3, to: 4 },
];

const CenterMap = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animFrame: number;
    let t = 0;

    const draw = () => {
      const w = canvas.width = canvas.offsetWidth * 2;
      const h = canvas.height = canvas.offsetHeight * 2;
      ctx.clearRect(0, 0, w, h);

      // Grid lines
      ctx.strokeStyle = "rgba(123, 51, 126, 0.08)";
      ctx.lineWidth = 1;
      for (let i = 0; i < w; i += 40) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, h);
        ctx.stroke();
      }
      for (let i = 0; i < h; i += 40) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(w, i);
        ctx.stroke();
      }

      // Connections (animated flowing lines)
      connections.forEach(({ from, to }) => {
        const a = hospitals[from];
        const b = hospitals[to];
        const x1 = (a.x / 100) * w;
        const y1 = (a.y / 100) * h;
        const x2 = (b.x / 100) * w;
        const y2 = (b.y / 100) * h;

        const gradient = ctx.createLinearGradient(x1, y1, x2, y2);
        gradient.addColorStop(0, "rgba(102, 103, 171, 0.6)");
        gradient.addColorStop(0.5, "rgba(123, 51, 126, 0.8)");
        gradient.addColorStop(1, "rgba(102, 103, 171, 0.6)");

        ctx.strokeStyle = gradient;
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 8]);
        ctx.lineDashOffset = -t * 0.5;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Flowing dot
        const progress = ((t * 0.005) % 1);
        const dotX = x1 + (x2 - x1) * progress;
        const dotY = y1 + (y2 - y1) * progress;
        ctx.fillStyle = "rgba(245, 213, 224, 0.9)";
        ctx.beginPath();
        ctx.arc(dotX, dotY, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 15;
        ctx.shadowColor = "rgba(123, 51, 126, 0.8)";
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      // Hospital nodes
      hospitals.forEach((hosp) => {
        const x = (hosp.x / 100) * w;
        const y = (hosp.y / 100) * h;

        // Isochrone ring
        if (hosp.pulse) {
          const ringRadius = 30 + Math.sin(t * 0.03) * 8;
          ctx.strokeStyle = `rgba(123, 51, 126, ${0.15 + Math.sin(t * 0.03) * 0.1})`;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(x, y, ringRadius, 0, Math.PI * 2);
          ctx.stroke();

          const ringRadius2 = 50 + Math.sin(t * 0.02) * 10;
          ctx.strokeStyle = `rgba(102, 103, 171, ${0.08 + Math.sin(t * 0.02) * 0.05})`;
          ctx.beginPath();
          ctx.arc(x, y, ringRadius2, 0, Math.PI * 2);
          ctx.stroke();
        }

        // Node
        const glowSize = hosp.pulse ? 12 + Math.sin(t * 0.04) * 3 : 8;
        ctx.shadowBlur = 20;
        ctx.shadowColor = "rgba(123, 51, 126, 0.6)";
        ctx.fillStyle = hosp.pulse ? "rgba(245, 213, 224, 0.9)" : "rgba(102, 103, 171, 0.7)";
        ctx.beginPath();
        ctx.arc(x, y, glowSize, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // Inner dot
        ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      });

      // Isochrone ring labels workaround: use hospital y for position
      hospitals.forEach((hospital) => {
        const x = (hospital.x / 100) * w;
        const yPos = (hospital.y / 100) * h;
        ctx.fillStyle = "rgba(245, 213, 224, 0.7)";
        ctx.font = `${11 * 2}px Rajdhani`;
        ctx.textAlign = "center";
        ctx.fillText(hospital.name, x, yPos + 25);
      });

      t++;
      animFrame = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animFrame);
  }, []);

  return (
    <motion.div
      className="glass-panel relative h-full overflow-hidden"
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.6, delay: 0.3 }}
    >
      <div className="absolute top-4 left-4 z-10">
        <span className="font-display text-xs tracking-[0.2em] text-muted-foreground">
          LIVE LOGISTICS MAP
        </span>
      </div>
      <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-glow-pink animate-pulse" />
        <span className="font-body text-xs text-muted-foreground">LIVE</span>
      </div>
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ imageRendering: "auto" }}
      />
    </motion.div>
  );
};

export default CenterMap;
