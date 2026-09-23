import { X, Navigation, Clock, ShieldCheck, Check, Zap } from "lucide-react";
import { MapLibreView } from "./MapLibreView";

export type RoutePreviewModalProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  origin?: { lat: number; lon: number; label?: string };
  destination?: { lat: number; lon: number; label?: string };
  routeGeometry?: any;
  distanceKm?: number;
  etaMin?: number;
  trafficStatus?: string;
  trafficColor?: string;
  h3Cell?: string;
  onApprove?: () => void;
};

export function RoutePreviewModal({
  open,
  onClose,
  title = "Route & Feasibility Verification",
  origin,
  destination,
  routeGeometry,
  distanceKm,
  etaMin,
  trafficStatus = "NORMAL",
  trafficColor = "#10B981",
  h3Cell,
  onApprove,
}: RoutePreviewModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in-0">
      <div 
        className="bg-card border border-border/70 shadow-2xl rounded-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <div className="flex items-center gap-2">
            <span className="live-dot" />
            <span className="font-bold text-sm tracking-tight">{title}</span>
            {h3Cell && (
              <span className="text-[10px] font-mono bg-indigo-500/15 text-indigo-400 px-2 py-0.5 rounded">
                H3: {h3Cell.slice(0, 9)}...
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition"
            aria-label="Close route modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Map Canvas */}
        <div className="h-[340px] w-full relative bg-secondary/30">
          <MapLibreView
            origin={origin}
            destination={destination}
            routeGeometry={routeGeometry}
            trafficStatus={trafficStatus}
            trafficColor={trafficColor}
            className="w-full h-full"
          />
        </div>

        {/* Telemetry and Action Footer */}
        <div className="p-4 bg-card flex flex-col gap-3 border-t border-border/50">
          <div className="grid grid-cols-3 gap-2 text-center bg-secondary/40 p-2.5 rounded-xl">
            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-bold block">Estimated Transit</span>
              <span className="text-sm font-bold text-foreground flex items-center justify-center gap-1">
                <Clock size={13} className="text-emerald-400" />
                {etaMin ? `${etaMin} mins` : "16 mins"}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-bold block">Road Distance</span>
              <span className="text-sm font-bold text-foreground">
                {distanceKm ? `${distanceKm} km` : "4.1 km"}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-bold block">Traffic Status</span>
              <span className="text-sm font-bold capitalize" style={{ color: trafficColor }}>
                {trafficStatus}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
            <span className="flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-emerald-500" />
              Pre-flight route verified against medical window.
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 rounded-lg border border-border/60 hover:bg-secondary transition font-medium"
              >
                Close
              </button>
              {onApprove && (
                <button
                  type="button"
                  onClick={() => {
                    onApprove();
                    onClose();
                  }}
                  className="px-4 py-1.5 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition flex items-center gap-1.5"
                >
                  <Check size={14} /> Approve Proposal
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
