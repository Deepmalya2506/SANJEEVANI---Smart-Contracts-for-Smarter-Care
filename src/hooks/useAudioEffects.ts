import { useEffect, useRef, useState, useCallback } from "react";

const CLICK_FREQ = 1200;
const CLICK_DURATION = 0.06;
const HOVER_FREQ = 800;
const HOVER_DURATION = 0.04;

export const useAudioEffects = () => {
  const ctxRef = useRef<AudioContext | null>(null);
  const bgRef = useRef<HTMLAudioElement | null>(null);
  const [musicOn, setMusicOn] = useState(false);

  const getCtx = useCallback(() => {
    if (!ctxRef.current) {
      ctxRef.current = new AudioContext();
    }
    return ctxRef.current;
  }, []);

  const playTone = useCallback((freq: number, dur: number, vol = 0.08) => {
    try {
      const ctx = getCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(vol, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
      osc.connect(gain).connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + dur);
    } catch {}
  }, [getCtx]);

  const playClick = useCallback(() => playTone(CLICK_FREQ, CLICK_DURATION, 0.06), [playTone]);
  const playHover = useCallback(() => playTone(HOVER_FREQ, HOVER_DURATION, 0.03), [playTone]);

  const toggleMusic = useCallback(() => {
    setMusicOn((prev) => {
      const next = !prev;
      if (next) {
        if (!bgRef.current) {
          bgRef.current = new Audio("/videos/bg-nature.mp4");
          bgRef.current.loop = true;
          bgRef.current.volume = 0.15;
        }
        bgRef.current.play().catch(() => {});
      } else {
        bgRef.current?.pause();
      }
      return next;
    });
  }, []);

  useEffect(() => {
    const handleClick = () => playClick();
    document.addEventListener("click", handleClick);
    return () => {
      document.removeEventListener("click", handleClick);
      bgRef.current?.pause();
    };
  }, [playClick]);

  return { musicOn, toggleMusic, playClick, playHover };
};
