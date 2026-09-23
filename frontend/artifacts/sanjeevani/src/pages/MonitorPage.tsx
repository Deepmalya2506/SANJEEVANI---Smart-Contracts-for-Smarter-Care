import { useState, useEffect } from "react";
import { 
  Truck, 
  CheckCircle2, 
  Clock, 
  ShieldCheck, 
  MapPin, 
  ArrowRight,
  PackageCheck,
  AlertCircle,
  Zap
} from "lucide-react";
import { MapLibreView } from "@/components/map/MapLibreView";
import { getGisRoute } from "@/lib/api";

export function MonitorPage() {
  const [loanStatus, setLoanStatus] = useState<"DISPATCHED" | "DELIVERED">("DISPATCHED");
  const [routeData, setRouteData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Default active loan coordinates: Aster Medisource (Lender) -> St. Martha Medical Centre (Borrower)
  const lenderLocation = { lat: 22.5850, lon: 88.3750, label: "Aster Medisource (Lender)" };
  const borrowerLocation = { lat: 22.5726, lon: 88.3639, label: "St. Martha Medical Centre (Borrower)" };

  useEffect(() => {
    async function fetchRoute() {
      setLoading(true);
      try {
        const res = await getGisRoute({
          source: { lat: lenderLocation.lat, lon: lenderLocation.lon },
          destination: { lat: borrowerLocation.lat, lon: borrowerLocation.lon },
        });
        setRouteData(res.data || res);
      } catch {
        // Fallback route coordinates
        setRouteData({
          distance: 2400,
          duration: 720,
          traffic_adjusted_eta_min: 12.0,
          traffic_status: "NORMAL",
          traffic_color: "#10B981",
          geometry: {
            type: "LineString",
            coordinates: [
              [88.3750, 22.5850],
              [88.3700, 22.5790],
              [88.3639, 22.5726],
            ],
          },
        });
      } finally {
        setLoading(false);
      }
    }
    fetchRoute();
  }, []);

  const waypoints = [
    {
      title: "Equipment Reserved & Smart Contract Committed",
      time: "09:20 IST",
      status: "COMPLETED",
      description: "Escrow funds locked on EVM testnet, Terms hash verified.",
    },
    {
      title: "Dispatched from Aster Medisource",
      time: "09:28 IST",
      status: "COMPLETED",
      description: "Asset verified: OxyFlow 5L Concentrator (SN: OF-2024-88).",
    },
    {
      title: "In Transit — Kolkata Central Corridor",
      time: "09:35 IST",
      status: loanStatus === "DELIVERED" ? "COMPLETED" : "CURRENT",
      description: "Current speed 32 km/h. Traffic status: NORMAL.",
    },
    {
      title: "Delivery & Biomedical Handshake",
      time: loanStatus === "DELIVERED" ? "09:42 IST" : "Est. 09:44 IST",
      status: loanStatus === "DELIVERED" ? "COMPLETED" : "PENDING",
      description: "Acceptance scan and custody transfer at St. Martha.",
    },
  ];

  return (
    <div className="workspace h-[calc(100vh-80px)] flex flex-col p-4 md:p-6 gap-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="live-dot" />
            <span className="eyebrow">ACTIVE DISPATCH TRACKER · LOAN #LN-7741</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Live Dispatch-to-Delivery Route Tracker</h1>
          <p className="text-xs md:text-sm text-muted-foreground">
            End-to-end waypoint tracking and real-time transit telemetry between lender and borrower.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
            loanStatus === "DELIVERED"
              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
              : "bg-blue-500/15 text-blue-400 border border-blue-500/30 animate-pulse"
          }`}>
            {loanStatus === "DELIVERED" ? "DELIVERED & ACTIVE" : "IN TRANSIT"}
          </span>

          <button
            type="button"
            onClick={() => setLoanStatus(loanStatus === "DISPATCHED" ? "DELIVERED" : "DISPATCHED")}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition flex items-center gap-1.5"
          >
            {loanStatus === "DISPATCHED" ? (
              <>
                <PackageCheck size={14} /> Confirm Delivery
              </>
            ) : (
              <>
                <Zap size={14} /> Reset to In-Transit
              </>
            )}
          </button>
        </div>
      </div>

      {/* Grid: Live Map + Waypoints Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-0">
        {/* Left: Interactive Live Route Map */}
        <div className="lg:col-span-8 bg-card/40 border border-border/50 rounded-xl overflow-hidden relative flex flex-col">
          <div className="flex-1 min-h-[400px]">
            <MapLibreView
              origin={{
                lat: lenderLocation.lat,
                lon: lenderLocation.lon,
                label: lenderLocation.label,
              }}
              destination={{
                lat: borrowerLocation.lat,
                lon: borrowerLocation.lon,
                label: borrowerLocation.label,
              }}
              routeGeometry={routeData?.geometry}
              trafficStatus={routeData?.traffic_status || "NORMAL"}
              trafficColor={routeData?.traffic_color || "#10B981"}
              className="w-full h-full min-h-[420px]"
            />
          </div>

          {/* Bottom Transit Metric Strip */}
          <div className="bg-card/85 backdrop-blur border-t border-border/50 p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                Estimated Arrival
              </span>
              <span className="text-base font-bold text-foreground flex items-center gap-1">
                <Clock size={14} className="text-emerald-400" />
                {loanStatus === "DELIVERED" ? "Delivered" : `${routeData?.traffic_adjusted_eta_min || 12} mins`}
              </span>
            </div>

            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                Total Road Distance
              </span>
              <span className="text-base font-bold text-foreground">
                {Math.round((routeData?.distance || 2400) / 100) / 10} km
              </span>
            </div>

            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                Corridor Traffic
              </span>
              <span className="text-base font-bold text-emerald-400 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                {routeData?.traffic_status || "NORMAL"}
              </span>
            </div>

            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                Escrow Guarantee
              </span>
              <span className="text-base font-bold text-indigo-400 flex items-center gap-1">
                <ShieldCheck size={14} /> ₹1,850 Held
              </span>
            </div>
          </div>
        </div>

        {/* Right: Waypoint Checkpoints & Asset Manifest */}
        <aside className="lg:col-span-4 flex flex-col gap-4 overflow-y-auto">
          {/* Asset Card */}
          <div className="bg-card/70 border border-border/50 rounded-xl p-4 flex flex-col gap-2.5">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Asset in Custody
            </span>
            <div className="flex items-center justify-between">
              <div>
                <strong className="text-sm font-bold block">OxyFlow 5L Concentrator</strong>
                <span className="text-xs text-muted-foreground">Serial No: OF-2024-88 · Class II Medical</span>
              </div>
              <span className="text-xs font-bold bg-secondary px-2.5 py-1 rounded">
                Qty: 1
              </span>
            </div>
            <div className="text-[11px] text-muted-foreground border-t border-border/40 pt-2 flex justify-between">
              <span>Lender: Aster Medisource</span>
              <span>Borrower: St. Martha</span>
            </div>
          </div>

          {/* Waypoints Timeline */}
          <div className="bg-card/70 border border-border/50 rounded-xl p-4 flex-1 flex flex-col gap-3">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <Truck size={14} /> Delivery Milestones
            </span>

            <div className="flex flex-col gap-4 pt-2">
              {waypoints.map((wp, idx) => (
                <div key={wp.title} className="flex gap-3 relative">
                  {idx < waypoints.length - 1 && (
                    <div className="absolute left-[11px] top-6 bottom-[-16px] w-[2px] bg-border/60" />
                  )}
                  <div className="mt-0.5 z-10">
                    {wp.status === "COMPLETED" ? (
                      <CheckCircle2 size={22} className="text-emerald-500 fill-emerald-500/20" />
                    ) : wp.status === "CURRENT" ? (
                      <div className="w-[22px] h-[22px] rounded-full border-2 border-blue-500 flex items-center justify-center bg-blue-500/20 animate-pulse">
                        <div className="w-2 h-2 rounded-full bg-blue-500" />
                      </div>
                    ) : (
                      <div className="w-[22px] h-[22px] rounded-full border-2 border-border/70 flex items-center justify-center bg-background/50">
                        <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground/50" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 text-xs">
                    <div className="flex items-center justify-between font-semibold text-foreground">
                      <span>{wp.title}</span>
                      <span className="text-[10px] text-muted-foreground font-mono">{wp.time}</span>
                    </div>
                    <p className="text-muted-foreground text-[11px] mt-0.5">{wp.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
