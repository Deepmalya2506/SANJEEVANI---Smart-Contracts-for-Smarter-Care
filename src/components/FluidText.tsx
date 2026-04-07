import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useRef, useCallback } from "react";

const translations = [
  { text: "Sanjeevani", lang: "English" },
  { text: "संजीवनी", lang: "Hindi" },
  { text: "সঞ্জীবনী", lang: "Bengali" },
  { text: "సంజీవని", lang: "Telugu" },
  { text: "சஞ்சீவனி", lang: "Tamil" },
  { text: "ಸಂಜೀವನಿ", lang: "Kannada" },
  { text: "സഞ്ജീവനി", lang: "Malayalam" },
  { text: "સંજીવની", lang: "Gujarati" },
  { text: "ਸੰਜੀਵਨੀ", lang: "Punjabi" },
  { text: "ସଞ୍ଜୀବନୀ", lang: "Odia" },
  { text: "संजीवनी", lang: "Marathi" },
  { text: "سنجیونی", lang: "Urdu" },
  { text: "সঞ্জীৱনী", lang: "Assamese" },
];

const INTERVAL = 3000;

const FluidText = () => {
  const [index, setIndex] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Array<{
    x: number; y: number; vx: number; vy: number;
    tx: number; ty: number; alpha: number; size: number;
    hue: number;
  }>>([]);
  const animRef = useRef<number>(0);
  const phaseRef = useRef(0); // 0 = forming, 1 = hold, 2 = dissolve

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % translations.length);
    }, INTERVAL);
    return () => clearInterval(timer);
  }, []);

  const getTextParticles = useCallback((text: string, canvas: HTMLCanvasElement) => {
    const ctx = canvas.getContext("2d")!;
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.scale(dpr, dpr);

    const fontSize = Math.min(w * 0.12, 80);
    ctx.font = `300 ${fontSize}px -apple-system, BlinkMacSystemFont, "SF Pro Display", "Noto Sans Devanagari", "Noto Sans Bengali", "Noto Sans Tamil", "Noto Sans Telugu", "Noto Sans Kannada", "Noto Sans Malayalam", "Noto Sans Gujarati", "Noto Sans Gurmukhi", "Noto Sans Oriya", sans-serif`;
    ctx.fillStyle = "#fff";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, w / 2, h / 2);
    ctx.restore();

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const points: { x: number; y: number }[] = [];
    const gap = 3;

    for (let y = 0; y < canvas.height; y += gap) {
      for (let x = 0; x < canvas.width; x += gap) {
        const i = (y * canvas.width + x) * 4;
        if (imageData.data[i + 3] > 128) {
          points.push({ x: x / dpr, y: y / dpr });
        }
      }
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return points;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    const targets = getTextParticles(translations[index].text, canvas);
    const particles = particlesRef.current;
    const w = rect.width;
    const h = rect.height;

    // Reuse or create particles
    while (particles.length < targets.length) {
      particles.push({
        x: w / 2 + (Math.random() - 0.5) * w,
        y: h / 2 + (Math.random() - 0.5) * h,
        vx: 0, vy: 0,
        tx: 0, ty: 0,
        alpha: 0,
        size: Math.random() * 1.5 + 0.5,
        hue: 260 + Math.random() * 60,
      });
    }
    particles.length = targets.length;

    targets.forEach((t, i) => {
      particles[i].tx = t.x;
      particles[i].ty = t.y;
    });

    phaseRef.current = 0;
    let startTime = performance.now();

    const ctx = canvas.getContext("2d")!;

    const animate = (time: number) => {
      const elapsed = time - startTime;
      const dur = INTERVAL;

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      const scale = dpr;
      ctx.scale(scale, scale);

      for (const p of particles) {
        // Fluid spring dynamics
        const dx = p.tx - p.x;
        const dy = p.ty - p.y;
        const spring = 0.06;
        const damping = 0.85;

        p.vx += dx * spring;
        p.vy += dy * spring;
        p.vx *= damping;
        p.vy *= damping;

        // Add subtle turbulence
        p.vx += Math.sin(time * 0.002 + p.y * 0.01) * 0.15;
        p.vy += Math.cos(time * 0.002 + p.x * 0.01) * 0.15;

        p.x += p.vx;
        p.y += p.vy;

        // Alpha based on phase
        if (elapsed < dur * 0.2) {
          p.alpha = Math.min(1, p.alpha + 0.05);
        } else if (elapsed > dur * 0.75) {
          p.alpha = Math.max(0, p.alpha - 0.04);
        } else {
          p.alpha = Math.min(1, p.alpha + 0.02);
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${p.hue}, 60%, 75%, ${p.alpha * 0.9})`;
        ctx.fill();

        // Glow
        if (p.alpha > 0.5) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size * 2.5, 0, Math.PI * 2);
          ctx.fillStyle = `hsla(${p.hue}, 70%, 80%, ${p.alpha * 0.15})`;
          ctx.fill();
        }
      }

      ctx.restore();
      animRef.current = requestAnimationFrame(animate);
    };

    animRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animRef.current);
  }, [index, getTextParticles]);

  return (
    <div className="relative w-full max-w-3xl mx-auto" style={{ height: "140px" }}>
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ imageRendering: "auto" }}
      />
      <AnimatePresence mode="wait">
        <motion.span
          key={index}
          className="absolute bottom-0 left-1/2 -translate-x-1/2 text-xs tracking-[0.3em] text-muted-foreground/50 uppercase font-body"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4 }}
        >
          {translations[index].lang}
        </motion.span>
      </AnimatePresence>
    </div>
  );
};

export default FluidText;
