import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import logo from "@/assets/sanjeevani-logo.png";

const loadingSteps = [
  "Initializing neural network...",
  "Connecting to hospital grid...",
  "Mapping logistics routes...",
  "AI systems online.",
];

const LoadingScreen = ({ onComplete }: { onComplete: () => void }) => {
  const [step, setStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) {
          clearInterval(interval);
          setTimeout(onComplete, 600);
          return 100;
        }
        return p + 1.5;
      });
    }, 40);
    return () => clearInterval(interval);
  }, [onComplete]);

  useEffect(() => {
    const idx = Math.min(Math.floor(progress / 25), loadingSteps.length - 1);
    setStep(idx);
  }, [progress]);

  return (
    <motion.div
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-background"
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8, ease: "easeInOut" }}
    >
      {/* Video background with overlay */}
      <video
        autoPlay
        muted
        loop
        playsInline
        className="absolute inset-0 w-full h-full object-cover opacity-30"
      >
        <source src="/videos/bg-ocean.mp4" type="video/mp4" />
      </video>
      <div className="absolute inset-0 bg-gradient-to-b from-background/80 via-background/60 to-background/90" />

      <div className="relative z-10 flex flex-col items-center gap-8">
        <motion.img
          src={logo}
          alt="Sanjeevani"
          className="w-32 h-auto drop-shadow-[0_0_30px_hsl(280,70%,60%)]"
          animate={{ scale: [1, 1.05, 1], opacity: [0.8, 1, 0.8] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />

        <motion.h1
          className="font-display text-3xl md:text-4xl tracking-[0.3em] glow-text text-foreground"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          SANJEEVANI
        </motion.h1>

        <div className="w-64 md:w-80">
          <div className="h-1 rounded-full bg-muted overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{
                background: "linear-gradient(90deg, hsl(280,70%,60%), hsl(235,60%,55%), hsl(320,50%,88%))",
                width: `${progress}%`,
              }}
              transition={{ ease: "linear" }}
            />
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.p
            key={step}
            className="font-body text-sm tracking-widest text-muted-foreground"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.3 }}
          >
            {loadingSteps[step]}
          </motion.p>
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default LoadingScreen;
